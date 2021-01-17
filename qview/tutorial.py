import tkinter as tk

tutorials = [
    {'title': 'Selecting a job',
     'image': '',
     'what': 'All functionality for specific jobs are based on your selecting a job.',
     'how': 'Select a job by clicking on in the queue window. Once clicked, you can see the currently selected PID in the Status Panel.'},
    {'title': 'Getting the queue',
     'image': None,
     'what': 'You can print the queue, each job color coded by its job status. Pending jobs are yellow, running jobs are green, completed jobs are blue, timeouted jobs are red, and other jobs are white.',
     'how': 'Press the cow torso button to get the queue.'},
    {'title': 'Select user',
     'image': '',
     'what': 'You can fetch the queue from all users on the cluster.',
     'how': 'Start typing a username in the textbox, and a list of matching usernames will appear. Press <Enter> to select the user and fetch queue, or <Right Arrow> to select without fetching the queue. Pressing <Enter> while in the textbox will fetch the queue.'},
    {'title': 'Filter the queue',
     'image': '',
     'what': 'You can filter the queue by job status, submit time, and partition.',
     'how': 'Set the filter like youj wish, and then fetch the queue to apply them.'},
    {'title': 'Opening files in internal viewer',
     'image': '',
     'what': 'You can open input, output, error and and submit scripts associated with a job.',
     'how': ''},
    {'title': 'Open files in external viewer',
     'image': '',
     'what': '',
     'how': ''},
    {'title': '',
     'image': '',
     'what': '',
     'how': ''},
    {'title': '',
     'image': '',
     'what': '',
     'how': ''},
    {'title': '',
     'image': '',
     'what': '',
     'how': ''},
    {'title': '',
     'image': '',
     'what': '',
     'how': ''},
    {'title': '',
     'image': '',
     'what': '',
     'how': ''}
]


class Tutorial(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.images = self.parent.parent.images
        self.dir_image = self.parent.parent.dir_imag

        self.what = tk.StringVar()
        self.how = tk.StringVar()
        self.where = tk.StringVar()
        self.wraplength = 200

        self.create_widgets()

    def create_widgets(self):
        self.frame_top = tk.Frame(self)
        self.frame_menu = tk.Frame(self)
        self.frame_what = tk.Frame(self)
        self.frame_how = tk.Frame(self)
        self.frame_where = tk.Frame(self)
        self.frame_bottom = tk.Frame(self)

        self.frame_top.grid(row=0, column=0, columnspan=3, sticky=tk.N)
        self.frame_menu.grid(row=1, column=0, sticky=tk.N)
        self.frame_what.grid(row=1, column=1, sticky=tk.N)
        self.frame_how.grid(row=1, column=2, sticky=tk.N)
        self.frame_where.grid(row=1, column=3, sticky=tk.N)
        self.frame_bottom.grid(row=2, column=3, columnspan=3, sticky=tk.N)

        tk.Label(self.frame_top, text='Welcome to the Tutorial!').grid(row=0, column=0)

        self.menu = tk.Listbox(self.frame_menu)
        self.menu.grid(row=0, column=0)
        self.menu.bind('<Button-1>', self.menu_on_click)
        for toot in tutorials:
            self.menu.insert(tk.END, toot['title'])

        tk.Label(self.frame_what, text='What').grid(row=0, column=0, sticky=tk.N)
        tk.Label(self.frame_what, textvariable=self.what, wraplength=self.wraplength, justify=tk.LEFT).grid(row=1, column=0, sticky=tk.N)

        tk.Label(self.frame_how, text='How').grid(row=0, column=0, sticky=tk.N)
        tk.Label(self.frame_how, textvariable=self.how, wraplength=self.wraplength, justify=tk.LEFT).grid(row=1, column=0, sticky=tk.N)

        tk.Label(self.frame_where, text='Where').grid(row=0, column=0, sticky=tk.N)
        tk.Label(self.frame_where, image=None).grid(row=1, column=0, sticky=tk.N)

    def load_tutorial(self, toot):
        self.what.set(toot['what'])
        self.how.set(toot['how'])

    def menu_on_click(self, event):
        index = self.menu.index(f'@{event.x},{event.y}')
        title = self.menu.get(index)
        self.load_tutorial(self.fetch_tutorial(title))

    def fetch_tutorial(self, title):
        for toot in tutorials:
            if toot['title'] == title:
                return toot