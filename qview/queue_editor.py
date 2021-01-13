import tkinter as tk
from custom_widgets import QueueViewer, MyFrame


class QueueEditor(tk.Toplevel):
    def __init__(self, parent, qhandler):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.resizable(False, False)
        self.qhandler = qhandler
        self.headers = self.qhandler.headers

        self.themes = [
            {'id': 1,
             'name': 'For n00bz',
             'headers': 'jobid name'
             },
            {'id': 2,
             'name': 'Mediocre',
             'headers': 'jobid name timeleft username'
             },
            {'id': 3,
             'name': 'For 1337z',
             'headers': 'jobid name username timeleft timelimit numnodes numcpus partition submittime nodelist'}
        ]

        self.create_widgets()

        self.available_headers.bind('<Double-Button-1>', self.activate)
        self.active_headers.bind('<Double-Button-1>', self.deactivate)

    def create_widgets(self):
        self.topleft = MyFrame(self)
        self.topright = MyFrame(self)
        self.mid = MyFrame(self)
        self.bottom = MyFrame(self)

        self.bottom.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.topleft.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.mid.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.topright.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        tk.Label(self.topleft, text='Available headers').pack(fill=tk.BOTH, expand=True)
        tk.Label(self.topright, text='Active headers').pack(fill=tk.BOTH, expand=True)

        self.available_headers = tk.Listbox(self.topleft)
        self.active_headers = tk.Listbox(self.topright)
        self.queue_window = QueueViewer(self.bottom)

        self.queue_window.pack(side=tk.BOTTOM)

        self.active_headers.pack(fill=tk.BOTH, expand=True)
        tk.Button(self.mid, text='Activate', command=self.activate).pack()
        tk.Button(self.mid, text='Deactivate', command=self.deactivate).pack()
        tk.Label(self.mid, text='---------').pack()
        tk.Button(self.mid, text='Move up', command=self.move_up).pack()
        tk.Button(self.mid, text='Move down', command=self.move_down).pack()
        tk.Label(self.mid, text='---------').pack()
        tk.Button(self.mid, text='Preview selection', command=self.preview).pack()
        tk.Label(self.mid, text='---------').pack()

        for t in self.themes:
            tk.Button(self.mid, text=f'Theme {t["id"]}: {t["name"]}', command=lambda headers=t["headers"].split(): self.set_theme(headers)).pack()

        tk.Label(self.mid, text='---------').pack()
        tk.Button(self.mid, text='Save and close', command=self.save).pack()

        self.available_headers.pack(fill=tk.BOTH, expand=True)

        # Insert active fields
        for i, header in enumerate(self.parent.parent.queue_format.get().split()):
            self.active_headers.insert(i, header)

        # Insert available fields
        for i, header in enumerate(sorted(self.headers)):
            if header not in self.parent.parent.queue_format.get().split():
                self.available_headers.insert(i, header)

    def set_theme(self, headers):
        avails = [self.available_headers.get(i) for i in range(self.available_headers.size())]

        self.active_headers.delete(0, self.active_headers.size())
        self.available_headers.delete(0, self.available_headers.size())

        for i, h in enumerate(headers):
            self.active_headers.insert(i, h)

        self.update_avails()

    def activate(self, event, index=None, header=None):
        if index is None and header is None:
            index, header = self.get_selection(self.available_headers)
        self.available_headers.delete(index)
        self.active_headers.insert(0, header)
        self.active_headers.selection_set(0)

    def deactivate(self, event, index=None, header=None):
        if index is None and header is None:
            index, header = self.get_selection(self.active_headers)
        self.active_headers.delete(index)
        self.update_avails()
        self.available_headers.selection_set(0)

    def update_avails(self):
        self.available_headers.delete(0, tk.END)
        for h in self.headers:
            if h not in [self.active_headers.get(i) for i in range(self.active_headers.size())]:
                self.available_headers.insert(tk.END, h)

    def move_up(self):
        index, header = self.get_selection(self.active_headers)
        if index != 0:
            self.active_headers.delete(index)
            self.active_headers.insert(index-1, header)
            self.active_headers.selection_set(index-1)

    def move_down(self):
        index, header = self.get_selection(self.active_headers)
        if index != self.active_headers.size():
            self.active_headers.delete(index)
            self.active_headers.insert(index+1, header)
            self.active_headers.selection_set(index+1)

    def get_selection(self, lb):
        return lb.curselection()[0], lb.get(lb.curselection())

    def preview(self):
        headers = [self.active_headers.get(i) for i in range(self.active_headers.size())]
        self.queue_window.display_queue(self.qhandler, headers)

    def save(self):
        headers = " ".join([self.active_headers.get(i) for i in range(self.active_headers.size())])
        self.parent.parent.queue_format.set(headers)
        self.destroy()
        self.parent.print_q()