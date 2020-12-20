import tkinter as tk


class ExternalViewer(tk.Toplevel):
    def __init__(self, parent, content, skip_to_end=False):
        tk.Toplevel.__init__(self)
        self.parent = parent
        self.master = self.parent.parent
        self.content = content
        self.skip_to_end = skip_to_end

        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.viewer = tk.Text(self.frame, height=self.master.winfo_screenheight())
        self.viewer.pack(fill=tk.BOTH, expand=True)
        self.viewer.insert(tk.END, content)

        if self.skip_to_end:
            self.viewer.see(tk.END)
