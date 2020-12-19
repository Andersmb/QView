import tkinter as tk
from tkinter.font import Font
from tkinter import messagebox
import os
import sys
import json
import tempfile
from pathlib import Path
import paramiko as pmk
from PIL import Image, ImageTk
from collections import OrderedDict
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from window_login import Login
from window_home import Home


####################
DEV = False
####################


class QueueGui(tk.Tk):
    """
    """
    def __init__(self):
        tk.Tk.__init__(self)
        self.name = "QueueGui4_DEV" if DEV else "QueueGui4"
        self.dir_root = Path(__file__).absolute().parent.parent
        self.dir_imag = self.dir_root.joinpath('images')
        self.file_tooltips = self.dir_root.joinpath('tooltips.json')
        self.file_prefs = self.dir_root.joinpath('preferences.json')
        self.tmpdir = Path(tempfile.mkdtemp())

        # Initialize tk variables
        self.startup = tk.BooleanVar()
        self.cluster = tk.StringVar()
        self.user = tk.StringVar()
        self.pwd = tk.StringVar()
        self.job_history_startdate = tk.StringVar()
        self.queue_format = tk.StringVar()
        self.open_in_separate_window = tk.BooleanVar()

        # Define defaults for user-changable settings
        self.defaults = {'fontsize_q': 10}

        # Load and apply prefs
        self.prefs = self.load_prefs()
        self.font_q = Font(family='Courier', size=self.prefs['fontsize_q'])
        self.set_current_prefs()

        # Set up SSH client
        self.ssh_client = pmk.SSHClient()
        self.ssh_client.set_missing_host_key_policy(pmk.AutoAddPolicy())

        # Assign defaults to tk variables
        self.startup.set(True)

        # Store locations of cluster scratch directories
        self.scratch = {'stallo': f'/global/work/{self.user.get()}/',
                        'fram': '/cluster/work/jobs',
                        'saga': '/cluster/work/jobs',
                        'betzy': '/cluster/work/jobs'}

        # Store image objects for buttons
        self.images = {'stallo': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_stallo_100.jpg'))),
                       "saga": ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_saga_100.jpg'))),
                       "fram": ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_fram_100.jpg'))),
                       "betzy": ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_betzy_100.png'))),
                       'cow': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cow_small.jpeg'))),
                       'icon_input': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_input.png'))),
                       'icon_output': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_output.png'))),
                       'icon_error': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_error.png'))),
                       'icon_job': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_job.png'))),
                       'icon_history': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_history.png'))),
                       'icon_stallo': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_stallo_60.jpg'))),
                       'icon_saga': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_saga_60.jpg'))),
                       'icon_fram': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_fram_60.jpg'))),
                       'icon_betzy': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('cluster_betzy_60.png'))),
                       'icon_scfconv': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_scfconv.png'))),
                       'icon_geomconv': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_geomconv.png'))),
                       'icon_cost': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_cost.png'))),
                       'icon_cpu': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_cpu.png'))),
                       'icon_avogadro': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_avogadro.png'))),
                       'icon_skull': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_skull.png'))),
                       'icon_toolbox': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_toolbox.png'))),
                       'icon_+': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_+.png'))),
                       'icon_-': ImageTk.PhotoImage(Image.open(self.dir_imag.joinpath('icon_-.png')))}

        # Load file containing tooltip messages
        self.tooltips = self.load_tooltips()

        # Store cluster information
        self.hostnames = OrderedDict({'stallo': 'stallo.uit.no',
                                      'fram': 'fram.sigma2.no',
                                      'saga': 'saga.sigma2.no',
                                      'betzy': 'betzy.sigma2.no'})

        # Initialize windows
        self.window_login = Login(self, self.startup.get())
        self.show_login()

        # Set startup protocol to False
        self.startup.set(False)

    def show_login(self):
        self.window_login.grid(row=0, column=0)
        if not self.startup:
            self.window_home.grid_forget()

    def show_home(self):
        self.window_login.grid_forget()
        self.window_home = Home(self)
        self.window_home.grid(row=0, column=0)

    def load_tooltips(self):
        with open(self.file_tooltips) as f:
            return json.load(f)

    def get_current_prefs(self):
        return {
            'fontsize_q': self.font_q.actual()['size'],
            'external_viewer': self.open_in_separate_window.get()
        }

    def set_current_prefs(self):
        self.open_in_separate_window.set(self.prefs['external_viewer'])

    def load_prefs(self):
        try:
            with open(self.file_prefs) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.defaults

    def dump_prefs(self):
        with open(self.file_prefs, 'w') as f:
            json.dump(self.get_current_prefs(), f)
        messagebox.showinfo(self.name, f'Preferences stored in {self.file_prefs}')


if __name__ == "__main__":
    app = QueueGui()
    print(f"Welcome to {app.name}: New session started")
    app.title(app.name)
    app.resizable(False, False)
    app.lift()
    app.mainloop()
