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
        self.configure(borderwidth=1, highlightthickness=0)


class MyText(tk.Text):
    def __init__(self, parent, **kwargs):
        tk.Text.__init__(self, parent, **kwargs)
        self.configure(highlightthickness=0, borderwidth=1, relief=tk.SUNKEN)