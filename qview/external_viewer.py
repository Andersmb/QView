import tkinter as tk
from custom_widgets import QueueViewer


class ExternalViewer(tk.Toplevel):
    def __init__(self, parent, qhandler, pid, ftype, skip_to_end=False):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.qhandler = qhandler
        self.pid = pid
        self.ftype = ftype
        self.skip_to_end = skip_to_end

        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(self, text='Refresh', command=self.refresh).pack()

        self.viewer = QueueViewer(self.frame)
        self.viewer.pack(fill=tk.BOTH, expand=True)
        self.viewer.display_file(self.qhandler, self.pid, self.ftype, skip_to_end=self.skip_to_end)

    def refresh(self):
        self.viewer.delete(1.0, tk.END)
        self.viewer.display_file(self.qhandler, self.pid, self.ftype, skip_to_end=self.skip_to_end)
