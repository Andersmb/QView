import tkinter as tk
from custom_widgets import QueueViewer


class ExternalViewer(tk.Toplevel):
    def __init__(self, parent, queue, pid, ftype):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.queue = queue
        self.pid = pid
        self.ftype = ftype

        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.viewer = QueueViewer(self.frame)
        self.viewer.pack(fill=tk.BOTH, expand=True)
        self.viewer.display_file(self.queue, self.pid, self.ftype)
