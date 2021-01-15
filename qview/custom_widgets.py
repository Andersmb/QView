import tkinter as tk


class ToolTipFunctionality:
    def __init__(self, wid):
        self.wid = wid
        self.widget_depth = 1
        self.widget_search_depth = 10

        self.bind('<Enter>', lambda event, i=1: self.on_enter(event, i))
        self.bind('<Leave>', lambda event: self.on_leave(event))

    def on_enter(self, event, i):
        if i > self.widget_search_depth:
            return
        try:
            cmd = f'self{".master"*i}.show_tooltip(self.wid)'
            eval(cmd)
            self.widget_depth = i
        except AttributeError:
            return self.on_enter(event, i+1)

    def on_leave(self, event):
        cmd = f'self{".master" * self.widget_depth}.hide_tooltip()'
        eval(cmd)


class MyButton(tk.Button, ToolTipFunctionality):
    def __init__(self, parent, wid, **kwargs):
        tk.Button.__init__(self, parent, **kwargs)
        ToolTipFunctionality.__init__(self, wid)

        self.configure(borderwidth=0, highlightthickness=1)


class MyLabel(tk.Label, ToolTipFunctionality):
    def __init__(self, parent, wid, **kwargs):
        tk.Label.__init__(self, parent, **kwargs)
        ToolTipFunctionality.__init__(self, wid)
        self.configure(borderwidth=0, highlightthickness=0)


class MyFrame(tk.Frame):
    def __init__(self, parent, highlight=True, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.configure(borderwidth=1 if highlight else 0, relief=tk.GROOVE)

        if highlight:
            self.bind('<Enter>', self.on_enter)
            self.bind('<Leave>', self.on_leave)

    def on_enter(self, event):
        self.configure(relief=tk.SUNKEN)

    def on_leave(self, event):
        self.configure(relief=tk.GROOVE)


class MyOptionMenu(tk.OptionMenu):
    def __init__(self, *args, **kwargs):
        tk.OptionMenu.__init__(self, *args, **kwargs)
        self['menu'].config(borderwidth=0)


class MyCheckbutton(tk.Checkbutton):
    def __init__(self, parent, **kwargs):
        tk.Checkbutton.__init__(self, parent, **kwargs)
        self.configure(borderwidth=0, highlightthickness=0)


class MyEntry(tk.Entry):
    def __init__(self, parent, **kwargs):
        tk.Entry.__init__(self, parent, **kwargs)
        self.configure(borderwidth=1, highlightthickness=0, selectbackground='#7a0a4b')


class AutoCompleteEntry(MyEntry):
    def __init__(self, parent, entries, **kwargs):
        MyEntry.__init__(self, parent, **kwargs)
        self.focus()
        self.entries = entries

        self.var = tk.StringVar()  # The var to match
        self['textvariable'] = self.var  # Associate a textvariable with the Entry
        self.var.trace_add('write', self.on_trace)  # Add observer to keep capture when self.var changes
        self.lb_exists = False  # Keep track of when the listbox exists

        self.bind('<Escape>', self.close_lb)
        self.bind('<Right>', self.select)
        self.bind('<Up>', lambda event: self.move('up', event))
        self.bind('<Down>', lambda event: self.move('down', event))

    def on_trace(self, name, index, mode):
        if self.var.get() == '':
            if self.lb_exists:
                self.lb.destroy()
                self.lb_exists = False
        else:
            matches = self.get_matches()
            if matches:
                if not self.lb_exists:
                    self.lb = tk.Listbox(width=self['width'],
                                         bg='#292b4a',
                                         fg='#b0c8ff',
                                         selectbackground='#6e3478')
                    self.lb.place(in_=self, relx=0, rely=1)
                    self.lb.bind('<Right>', self.select)
                    self.lb.bind('<Escape>', self.close_lb)
                    self.lb.bind('<Double-Button-1>', self.select)
                    self.lb_exists = True

                self.lb.delete(0, tk.END)
                for m in matches:
                    self.lb.insert(tk.END, m)
            else:
                if self.lb_exists:
                    self.lb.destroy()
                    self.lb_exists = False

    def move(self, direction, event):
        if not self.lb_exists:
            return
        if self.lb:
            if self.lb.curselection() == ():
                index = '-1'
            else:
                index = self.lb.curselection()[0]

            test = int(index) < self.lb.size()-1 if direction == 'down' else int(index) > 0
            if test:
                self.lb.selection_clear(index)
                index = str(int(index) + 1) if direction == 'down' else str(int(index) - 1)

                self.lb.see(index)
                self.lb.selection_set(index)
                self.lb.activate(index)

    def select(self, event):
        if self.lb_exists:
            self.var.set(self.lb.get(tk.ACTIVE))
            self.lb.destroy()
            self.lb_exists = False
            self.icursor(tk.END)
            self.focus_set()

    def close_lb(self, event):
        if self.lb_exists:
            self.lb.destroy()
            self.lb_exists = False

    def get_matches(self):
        return [e for e in self.entries if e.startswith(self.var.get())]


class QueueViewer(tk.Text):
    def __init__(self, parent, pid_var=None, **kwargs):
        tk.Text.__init__(self, parent, **kwargs)
        self.parent = parent
        self.pid_var = pid_var
        self.create_tags()
        self.configure(background='#000000', foreground='#ffffff', selectbackground='#7a0a4b', wrap=tk.NONE, cursor='dotbox')

        self.bind('<Motion>', self.on_motion)
        self.bind('<Button-1>', self.on_click)

        self.linenumber = tk.IntVar()
        self.linenumber.trace('w', self.on_trace)

    def display_queue(self, qhandler, headers):
        queue = qhandler.fetch()
        self.delete(0.1, tk.END)
        self.insert(tk.END, queue[headers])

        # Apply tags to color code
        for i, row in queue.iterrows():
            i -= queue.index[0]
            jobstate = qhandler.get_job(queue, row.jobid).state.iloc[0]
            self.tag_add(jobstate, f'{i + 2}.0', f'{i + 2}.{tk.END}')
            if i % 2 == 0:
                self.tag_add('evenline', f'{i+1}.0', f'{i+1}.{tk.END}')
            else:
                self.tag_add('oddline', f'{i+1}.0', f'{i+1}.{tk.END}')

    def display_file(self, qhandler, pid, ftype, skip_to_end=False):
        fname, content = qhandler.get_file_content(qhandler.fetch(), pid, ftype)

        self.delete(0.1, tk.END)
        self.insert(0.1, f'File path: {fname}\n')
        self.tag_add('filename', '0.0', f'2.{tk.END}')
        self.insert(tk.END, content)
        if skip_to_end:
            self.see(tk.END)

    def create_tags(self):
        tag_fg_colors = {
            'COMPLETED': '#717feb',
            'RUNNING': '#51c280',
            'PENDING': '#deb23a',
            'CANCELLED': '#d966d9',
            'TIMEOUT': '#de5f74',
            'filename': '#de7878'
        }
        tag_bg_colors = {
            'oddline': '#1f1f1f'
        }
        for status, color in tag_fg_colors.items():
            self.tag_configure(status, foreground=color)

        for status, color in tag_bg_colors.items():
            self.tag_configure(status, background=color)

        self.tag_configure('matched', background='#ffb0ab', foreground='#000000')
        self.tag_configure('active', background='#0e4536', foreground='#ffffff')

        self.tag_raise(tk.SEL)

    def find_all(self, pattern, tag, start="1.0", end='end', nocase=True, regexp=False):
        start = self.index(start)
        end = self.index(end)

        self.mark_set('match_start', start)
        self.mark_set('match_end', start)
        self.mark_set('search_limit', end)

        counter = tk.IntVar()
        while True:
            index = self.search(pattern=pattern, index='match_end', stopindex='search_limit', count=counter, regexp=regexp, nocase=nocase)
            if index == "":
                break
            if counter.get() == 0:
                break

            self.mark_set('match_start', index)
            self.mark_set('match_end', f'{index}+{counter.get()}c')
            self.tag_add(tag, 'match_start', 'match_end')

    def on_motion(self, event):
        x, y = self.index(f'@{event.x},{event.y}').split('.')
        self.linenumber.set(x)

    def on_trace(self, var, index, mode):
        buffer = range(1, 10, 1)
        i = self.linenumber.get()
        self.tag_add('active', f'{i}.0', f'{i}.{tk.END}')
        [self.tag_remove('active', f'{i-b}.0', f'{i-b}.{tk.END}') for b in buffer]
        [self.tag_remove('active', f'{i+b}.0', f'{i+b}.{tk.END}') for b in buffer]

    def on_click(self, event):
        x, y = self.index(f'@{event.x},{event.y}').split('.')
        try:
            pid = int(self.get(f'{x}.0', f'{x}.{tk.END}').split()[1])
            self.pid_var.set(pid)
        except (AttributeError, IndexError, ValueError):
            pass
