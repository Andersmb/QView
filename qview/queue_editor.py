import tkinter as tk


class QueueEditor(tk.Toplevel):
    def __init__(self, parent, fields):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.fields = fields

        self.create_widgets()

    def create_widgets(self):
        self.topleft = tk.Frame(self)
        self.topright = tk.Frame(self)
        self.mid = tk.Frame(self)
        self.bottom = tk.Frame(self)

        self.topleft.grid(row=0, column=0)
        self.mid.grid(row=0, column=1)
        self.topright.grid(row=0, column=2)
        self.bottom.grid(row=1, column=0)

        tk.Label(self.topleft, text='Available headers').pack()
        tk.Label(self.topright, text='Active labels').pack()

        self.avail = tk.Listbox(self.topleft)
        self.avail.grid(row=1, column=0)

        self.active = tk.Listbox(self.topright)
        self.active.grid(row=1, column=0)

        # Insert fields
        for i, field in enumerate(self.fields):
            self.avail.insert(i, field)

