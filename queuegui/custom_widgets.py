import tkinter as tk


class ToolTipFunctionality:
    def __init__(self, wid):
        self.wid = wid
        self.widet_depth = 1
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


class MyLabel(tk.Label, ToolTipFunctionality):
    def __init__(self, parent, wid, **kwargs):
        tk.Label.__init__(self, parent, **kwargs)
        ToolTipFunctionality.__init__(self, wid)

