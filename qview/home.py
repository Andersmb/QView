import time
import tkinter as tk
from datetime import datetime as dt, timedelta
from threading import Thread
from tkinter import messagebox, colorchooser
import re
import pyperclip as ppc

import paramiko as pmk
from custom_widgets import MyButton, MyLabel, MyFrame, MyEntry, MyCheckbutton, MyOptionMenu, QueueViewer, AutoCompleteEntry
from external_viewer import ExternalViewer
from queue import Queue
from queue_editor import QueueEditor
from tutorial import Tutorial
from helpers import from_val
from exceptions import *

# Define some constants
CONST_HISTORY_LENGTH = 14  # How long back to look at job history
CONST_MONITOR_IDLE_TIME = 0.5  # Frequency in sec of background monitoring


class Home(tk.Frame):
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.inner_pads = dict(padx=0, pady=2)  # Used for spacing widgets

        # Set up SSH client
        self.ssh_client, self.sftp_client = self.setup_remote_connection()

        # Variable for keeping track of SSH connection
        self.ssh_isalive = tk.BooleanVar()

        # Define some tkinter vars
        self.selected = tk.StringVar(); self.selected.set('')
        self.running_jobs = tk.IntVar(); self.running_jobs.set(0)
        self.pending_jobs = tk.IntVar(); self.pending_jobs.set(0)
        self.quser = tk.StringVar(); self.quser.set(self.parent.user.get())
        self.monitor_hostname = tk.StringVar(); self.monitor_hostname.set(self.parent.hostnames[self.parent.cluster.get()])
        self.search_all = tk.BooleanVar(); self.search_all.set(0)
        self.tooltip = tk.StringVar(); self.tooltip.set(self.parent.tooltips['idle'])
        self.timestamp = tk.StringVar()
        self.thread_ssh_alive = tk.BooleanVar()
        self.thread_job_alive = tk.BooleanVar()
        self.thread_sel_alive = tk.BooleanVar()
        self.queue_visible = tk.BooleanVar()

        # Define the job history length and set default to today
        self.job_history = [dt.today().date() - timedelta(days=i) for i in range(CONST_HISTORY_LENGTH)]
        self.parent.job_history_startdate.set(str(dt.today().date()))

        # Define partitions
        self.filter_partition = tk.StringVar()
        partitions = self.execute_remote('/usr/bin/sinfo --noheader -O partition').split()
        self.partitions = {key.split('*')[0]: key.split('*')[0] for key in partitions}  # Get rid of * symbol, normal*
        self.partitions['ALL'] = 'All partitions'
        self.filter_partition.set(self.partitions['ALL'])

        # Define the job status variables and set default to all jobs
        self.filter_job_status = tk.StringVar()
        self.job_stati = {'ALL': 'All jobs', 'RUNNING': 'Running', 'PENDING': 'Pending', 'COMPLETED': 'Completed', 'TIMEOUT': 'Timeout'}
        self.filter_job_status.set(self.job_stati['ALL'])

        # Create the widgets and set color
        self.create_widgets()
        self.set_color()

        # Start threads for background monitoring
        self.thread_jobs = Thread(target=self.monitor_running_pending_jobs, daemon=True)
        self.thread_timestamp = Thread(target=self.monitor_output_last_update, daemon=True)

        self.thread_jobs.start()
        self.thread_timestamp.start()

        # Bind events to Home
        self.bind_events()

        self.print_q()

    def create_widgets(self):
        self.grid(row=0, column=0, sticky=tk.NSEW)
        pads_inner = dict(padx=0, pady=1)
        pads_outer = dict(padx=5, pady=5)

        # Define frames for holding widgets
        self.frame_top = MyFrame(self, highlight=False)
        self.frame_top.grid(row=0, column=0, sticky=tk.NSEW)

        self.frame_toptools = MyFrame(self.frame_top)
        self.frame_visualization = MyFrame(self.frame_top)
        self.frame_filters = MyFrame(self.frame_top)
        self.frame_status = MyFrame(self.frame_top)
        self.frame_cluster = MyFrame(self.frame_top)
        self.frame_prefs = MyFrame(self.frame_top)
        self.frame_q = MyFrame(self, '', width=1000, height=300)
        self.frame_q.grid_propagate(False)
        self.frame_q.grid_rowconfigure(0, weight=1)
        self.frame_q.grid_columnconfigure(0, weight=1)
        self.frame_bottools = MyFrame(self)

        # Grid the frames
        self.frame_toptools.grid(row=0, column=0, sticky=tk.NSEW, **pads_outer)
        self.frame_visualization.grid(row=0, column=1, sticky=tk.NSEW, **pads_outer)
        self.frame_filters.grid(row=0, column=2, sticky=tk.NSEW, **pads_outer)
        self.frame_status.grid(row=0, column=3, sticky=tk.NSEW, **pads_outer)
        self.frame_cluster.grid(row=0, column=4, sticky=tk.NSEW, **pads_outer)
        self.frame_prefs.grid(row=0, column=5, sticky=tk.NSEW, **pads_outer)
        self.frame_q.grid(row=1, column=0, columnspan=6, sticky=tk.NSEW, **pads_outer)
        self.frame_bottools.grid(row=2, column=0, sticky=tk.NSEW, **pads_outer)

        # Top tools
        MyLabel(self.frame_toptools, 'label_tools', text="TOOLS").grid(row=0, column=0, columnspan=2, **pads_outer)
        MyButton(self.frame_toptools, 'button_print_q', image=self.parent.images['icon_queue'], width=60, height=60, command=self.print_q).grid(row=1, column=0, columnspan=2, **pads_inner)
        MyButton(self.frame_toptools, 'button_history', image=self.parent.images['icon_history'], width=60, height=60, command=self.notimplemented).grid(row=1, column=2, columnspan=2, **pads_inner)

        MyButton(self.frame_toptools, 'button_input', image=self.parent.images['icon_input'], width=30, height=30, command=lambda: self.print_file_contents('input')).grid(row=2, column=0, **pads_inner)
        MyButton(self.frame_toptools, 'button_output', image=self.parent.images['icon_output'], width=30, height=30, command=lambda: self.print_file_contents('output')).grid(row=2, column=1, **pads_inner)
        MyButton(self.frame_toptools, 'button_error', image=self.parent.images['icon_error'], width=30, height=30, command=lambda: self.print_file_contents('error')).grid(row=2, column=2, **pads_inner)
        MyButton(self.frame_toptools, 'button_job', image=self.parent.images['icon_job'], width=30, height=30, command=lambda: self.print_file_contents('job')).grid(row=2, column=3, **pads_inner)

        MyButton(self.frame_toptools, 'button_cost', image=self.parent.images['icon_cost'], width=30, height=30, command=self.notimplemented).grid(row=3, column=0, **pads_inner)
        MyButton(self.frame_toptools, 'button_cpu', image=self.parent.images['icon_cpu'], width=30, height=30, command=self.notimplemented).grid(row=3, column=1, **pads_inner)
        killbutton = MyButton(self.frame_toptools, 'button_killjob', image=self.parent.images['icon_killjob'], command=self.kill_job, width=30, height=30)
        killbutton.grid(row=3, column=2, **pads_inner)
        killbutton.bind('<Control-Button-1>', self.kill_job)
        MyButton(self.frame_toptools, 'button_tutorial', image=self.parent.images['icon_tutorial'], width=30, height=30, command=self.launch_tutorial).grid(row=3, column=3, **pads_inner)

        MyLabel(self.frame_visualization, 'label_visualization', text="VISUALS").grid(row=0, column=0, pady=5, padx=5)
        MyButton(self.frame_visualization, 'button_scfconv', image=self.parent.images['icon_scfconv'], width=50, height=50, command=self.notimplemented).grid(row=1, column=0, **pads_inner)
        MyButton(self.frame_visualization, 'button_geomconv', image=self.parent.images['icon_geomconv'], width=50, height=50, command=self.notimplemented).grid(row=2, column=0, **pads_inner)
        MyButton(self.frame_visualization, 'button_avogadro', image=self.parent.images['icon_avogadro'], width=50, height=50, command=self.notimplemented,
                  highlightbackground='black', highlightthickness=1).grid(row=3, column=0, **pads_inner)

        MyLabel(self.frame_filters, 'label_filters', text="FILTERS").grid(row=0, column=0, columnspan=2, **pads_outer)
        MyLabel(self.frame_filters, 'label_username', text='Username:').grid(row=1, column=0, sticky=tk.W, **pads_inner)
        self.entry_username = AutoCompleteEntry(self.frame_filters, self.get_all_users(), width=10)
        self.entry_username.grid(row=1, column=1, sticky=tk.W, **pads_inner)
        self.entry_username.insert(0, self.parent.user.get())
        self.entry_username.close_lb(None)

        MyLabel(self.frame_filters, 'label_jobstatus', text='Job status:').grid(row=2, column=0, sticky=tk.W, **pads_inner)
        MyOptionMenu(self.frame_filters, self.filter_job_status, *[val for key, val in self.job_stati.items()]).grid(row=2, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_filters, 'label_submitdate', text='Submit date:').grid(row=3, column=0, sticky=tk.W, **pads_inner)
        tk.OptionMenu(self.frame_filters, self.parent.job_history_startdate, *self.job_history).grid(row=3, column=1, sticky=tk.W, **pads_inner)

        MyLabel(self.frame_filters, 'label_partition', text='Partition:').grid(row=4, column=0, sticky=tk.W, **pads_inner)
        tk.OptionMenu(self.frame_filters, self.filter_partition, *[val for key, val in self.partitions.items()]).grid(row=4, column=1, sticky=tk.W, **pads_inner)

        self.label_search = MyLabel(self.frame_filters, 'label_search', text='Search ANY:')
        self.label_search.grid(row=5, column=0, sticky=tk.W, **pads_inner)
        self.label_search.bind('<Button-1>', self.update_search_mode)
        self.entry_search = MyEntry(self.frame_filters, width=10)
        self.entry_search.grid(row=5, column=1, sticky=tk.W, **pads_inner)

        MyLabel(self.frame_status, 'label_status', text="STATUS").grid(row=0, column=0, columnspan=2, **pads_outer)
        MyLabel(self.frame_status, 'label_hostname', text="Hostname:").grid(row=1, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.monitor_hostname).grid(row=1, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_selected', text="Selected PID:").grid(row=2, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.selected).grid(row=2, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_running', text="Running jobs:").grid(row=3, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.running_jobs).grid(row=3, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_pending', text="Pending jobs:").grid(row=4, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.pending_jobs).grid(row=4, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_jobworker', text='Job worker:').grid(row=5, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.thread_job_alive).grid(row=5, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_timestamp', text='Last update:').grid(row=6, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.timestamp).grid(row=6, column=1, sticky=tk.W, **pads_inner)

        MyLabel(self.frame_cluster, 'label_changecluster', text="CHANGE CLUSTER").grid(row=0, column=0, columnspan=2, **pads_outer)

        cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for cell, cluster in zip(cells, self.parent.hostnames.keys()):
            row, col = cell
            bgcolor = '#00de07' if cluster == self.parent.cluster.get() else 'black'
            edgethickness = 2 if cluster == self.parent.cluster.get() else 1
            relief = tk.SUNKEN if cluster == self.parent.cluster.get() else None
            MyButton(self.frame_cluster,
                     f'button_{cluster}',
                     image=self.parent.images[f'icon_{cluster}'],
                     command=lambda cluster=cluster: self.parent.window_login.authorize(cluster),
                     width=60, height=60,
                     highlightbackground=bgcolor, highlightthickness=edgethickness,
                     relief=relief).grid(row=row+1, column=col, **pads_inner)

        MyLabel(self.frame_prefs, 'label_preferences', text="PREFERENCES").grid(row=0, column=0, columnspan=3, **pads_outer)

        self.frame_prefs.sub_fontsize = tk.Frame(self.frame_prefs)
        self.frame_prefs.sub_fontsize.grid(row=1, column=0, sticky=tk.W)
        MyLabel(self.frame_prefs.sub_fontsize, 'label_fontsize', text='Queue fontsize:').grid(row=0, column=0, sticky=tk.W, **pads_inner)
        MyButton(self.frame_prefs.sub_fontsize, 'button_increasefont', image=self.parent.images['icon_+'], width=15, height=15, command=self.increase_fontsize).grid(row=0, column=1, sticky=tk.W, **pads_inner)
        MyButton(self.frame_prefs.sub_fontsize, 'button_decreasefont', image=self.parent.images['icon_-'], width=15, height=15, command=self.decrease_fontsize).grid(row=0, column=2, sticky=tk.W, **pads_inner)

        self.frame_prefs.external_viewer = tk.Frame(self.frame_prefs)
        self.frame_prefs.external_viewer.grid(row=2, column=0, sticky=tk.W)
        MyLabel(self.frame_prefs.external_viewer, 'label_externalviewer', text='Use external viewer: ').grid(row=2, column=0, sticky=tk.W, **pads_inner)
        MyCheckbutton(self.frame_prefs.external_viewer, text='', variable=self.parent.open_in_separate_window).grid(row=2, column=1, sticky=tk.W ,**pads_inner)

        self.frame_prefs.colors = tk.Frame(self.frame_prefs)
        self.frame_prefs.colors.grid(row=3, column=0, sticky=tk.W)
        MyLabel(self.frame_prefs.colors, 'label_backgroundcolor', text='Backg. color:').grid(row=3, column=0, sticky=tk.W, **pads_inner)
        self.entry_background_color = MyEntry(self.frame_prefs.colors, width=8)
        self.entry_background_color.grid(row=3, column=1, sticky=tk.W, **pads_inner)
        self.entry_background_color.insert(tk.END, self.parent.background_color.get())
        MyButton(self.frame_prefs.colors, 'button_colorpicker_bg', image=self.parent.images['icon_colorpicker'], width=20, height=20, command=lambda: self.colorpicker(where='bg')).grid(row=3, column=2, **pads_inner)

        MyLabel(self.frame_prefs.colors, 'label_foregroundcolor', text='Foreg. color:').grid(row=4, column=0, sticky=tk.W, **pads_inner)
        self.entry_foreground_color = MyEntry(self.frame_prefs.colors, width=8)
        self.entry_foreground_color.grid(row=4, column=1, sticky=tk.W, **pads_inner)
        self.entry_foreground_color.insert(tk.END, self.parent.foreground_color.get())
        MyButton(self.frame_prefs.colors, 'button_colorpicker_fg', image=self.parent.images['icon_colorpicker'], width=20, height=20, command=lambda: self.colorpicker(where='fg')).grid(row=4, column=2, **pads_inner)

        self.frame_prefs.sub_bottom = tk.Frame(self.frame_prefs)
        self.frame_prefs.sub_bottom.grid(row=99, column=0, sticky=tk.W)
        MyButton(self.frame_prefs.sub_bottom, 'button_queue_editor', image=self.parent.images['icon_edit_queue'], width=30, height=30, command=self.queue_editor, cursor='pencil').grid(row=0, column=0, sticky=tk.W, **pads_outer)
        MyButton(self.frame_prefs.sub_bottom, 'button_restore_defaults', image=self.parent.images['icon_defaults'], width=30, height=30, command=self.parent.restore_defaults).grid(row=0, column=1, sticky=tk.W, **pads_outer)
        MyButton(self.frame_prefs.sub_bottom, 'button_savepref', image=self.parent.images['icon_applysettings'], width=30, height=30, command=self.parent.dump_prefs, cursor='heart').grid(row=0, column=2, sticky=tk.W, **pads_outer)

        # Main queue Text widget
        self.qv = QueueViewer(self.frame_q, self.selected)
        self.qv.grid(row=0, column=0, sticky=tk.NSEW)
        self.qv.configure(font=self.parent.font_q)

        # Bottom tools
        MyButton(self.frame_bottools, 'button_quit', image=self.parent.images['icon_skull'], command=self.quit,
                 width=30, height=30, cursor='pirate').grid(row=0, column=0, sticky=tk.W, **pads_outer)
        MyButton(self.frame_bottools, 'button_toolbox', image=self.parent.images['icon_toolbox'],
                 command=self.notimplemented, width=30, height=30, highlightcolor='black', highlightthickness=1).grid(row=0, column=1, sticky=tk.W, **pads_outer)
        MyButton(self.frame_bottools, 'button_ssh', image=self.parent.images['icon_ssh'], width=30, height=30, command=lambda cluster=self.parent.cluster.get(): self.parent.window_login.authorize(cluster)).grid(row=0, column=2, **pads_outer)

        self.label_tooltip = MyLabel(self.frame_bottools, 'idle', text=f'ToolTip: {self.tooltip.get()}', bg='#1f4a46', fg='#ffffff')
        self.label_tooltip.grid(row=0, column=99, **pads_outer)

        # Pop-up menu when right clicking inside the queue window
        self.popup_menu = tk.Menu(self.qv, tearoff=0)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Copy path to input file to clipboard', command=lambda: self.copy_to_clipboard('input'))
        self.popup_menu.add_command(label='Copy path to output file to clipboard', command=lambda: self.copy_to_clipboard('output'))
        self.popup_menu.add_command(label='Copy path to error file to clipboard', command=lambda: self.copy_to_clipboard('error'))
        self.popup_menu.add_command(label='Copy path to job file to clipboard', command=lambda: self.copy_to_clipboard('job'))
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Kill job', command=self.kill_job)
        self.popup_menu.add_command(label='Kill all jobs', command=lambda: self.kill_job(event=1))
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Plot SCF convergence', command=self.notimplemented)
        self.popup_menu.add_command(label='Plot geometry convergence', command=self.notimplemented)
        self.popup_menu.add_command(label='Open output file with Avogadro', command=self.notimplemented)
        self.popup_menu.add_separator()

        self.qv.bind('<Button-2>', self.popup)

    def popup(self, event):
        if not self.queue_visible.get():
            return
        x, y = self.qv.index(f'@{event.x},{event.y}').split('.')
        pid = self.qv.get(f'{x}.0', f'{x}.{tk.END}').split()[1]
        self.selected.set(pid)
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, '')
        finally:
            self.popup_menu.grab_release()

    def copy_to_clipboard(self, ftype):
        qhandler = Queue(ssh_client=self.ssh_client, sftp_client=self.sftp_client, user=self.quser.get())
        queue = qhandler.fetch()
        if ftype == 'input':
            f = queue[queue.jobid == self.selected.get()].inputfile.item()
            print(f)
            ppc.copy(str(f))
        elif ftype == 'output':
            f = queue[queue.jobid == self.selected.get()].outputfile.item()
            print(f)
            ppc.copy(str(f))
        elif ftype == 'error':
            f = queue[queue.jobid == self.selected.get()].stderr.item()
            print(f)
            ppc.copy(str(f))
        elif ftype == 'job':
            f = queue[queue.jobid == self.selected.get()].command.item()
            print(f)
            ppc.copy(str(f))

    def queue_editor(self):
        qhandler = Queue(ssh_client=self.ssh_client, sftp_client=self.sftp_client, user='all')
        return QueueEditor(self, qhandler)

    def get_all_users(self):
        cluster = self.parent.cluster.get()
        if cluster == 'stallo':
            d = '/home'
        else:
            d = '/cluster/home'

        users = self.execute_remote(f'ls {d}').split()
        return users

    def colorpicker(self, where):
        rgb, hex = colorchooser.askcolor(parent=self, initialcolor=self.parent.defaults['background_color'])
        if where == 'bg':
            self.entry_background_color.delete(0, tk.END)
            self.entry_background_color.insert(0, hex)
        elif where == 'fg':
            self.entry_foreground_color.delete(0, tk.END)
            self.entry_foreground_color.insert(0, hex)

        self.set_color()

    def set_color(self, *args):
        bg = self.entry_background_color.get().lower()
        fg = self.entry_foreground_color.get().lower()
        if not all([re.match(r'^#(?:[0-9a-f]{3}){1,2}$', col) for col in [bg, fg]]):
            return messagebox.showerror('Error', 'Invalid Hex color code')

        self.parent.background_color.set(bg)
        self.parent.foreground_color.set(fg)

        frames, widgets = self.gather_children(self.winfo_children())
        frames.append(self)
        for widget in widgets:
            widget.configure(background=bg)
            widget.configure(foreground=fg)

            if isinstance(widget, tk.Entry):
                widget.configure(insertbackground=fg)
            elif isinstance(widget, tk.OptionMenu):
                widget['menu'].config(fg='black')
                widget.configure(fg='black')

        for frame in frames:
            frame.configure(background=self.parent.background_color.get())

    def kill_job(self, event=None):
        pid = self.selected.get()
        if not pid:
            return messagebox.showinfo(self.parent.name, 'No PID selected')
        if self.quser.get()!= self.parent.user.get():
            return messagebox.showerror('Error', 'You cannot kill another user\'s job.')

        if event is not None:
            if messagebox.askyesno('WARNING',
                                   "You are about to kill all jobs in your queue. Are you sure you want to do this?"):
                if messagebox.askyesno('WARNING', 'Just double checking. Kill all jobs?'):
                    self.execute_remote(f'scancel -u {self.parent.user.get()}')
        else:
            if messagebox.askyesno('Warning', f'Are you sure you want to kill job {pid}?'):
                self.execute_remote(f'scancel {pid}')
            else:
                print('Nothing happened')

    def gather_children(self, widgets, frames=[], children=[]):
        if not widgets:
            return frames, children
        widget = widgets.pop()
        if isinstance(widget, tk.Frame):
            frames.append(widget)
            for child in widget.winfo_children():
                widgets.append(child)
            return self.gather_children(widgets, frames=frames, children=children)
        else:
            if not isinstance(widget, tk.Text):
                children.append(widget)
            return self.gather_children(widgets, frames=frames, children=children)

    def increase_fontsize(self):
        s = self.parent.font_q.actual()['size'] + 1
        self.parent.font_q.configure(size=s)

    def decrease_fontsize(self):
        s = self.parent.font_q.actual()['size'] - 1
        self.parent.font_q.configure(size=max(s, 3))

    def notimplemented(self):
        return messagebox.showerror(self.parent.name, 'Not implemented')

    def change_cluster(self, cluster):
        curr_cluster = self.parent.cluster.get()
        try:
            self.parent.window_login.authorize(cluster)
            self.destroy()
        except pmk.ssh_exception.AuthenticationException:
            self.parent.cluster.set(curr_cluster)
            pass

    def set_search_all(self):
        self.search_all.set(1)
        self.label_search.config(text='Search ALL:')

    def set_search_any(self):
        self.search_all.set(0)
        self.label_search.config(text='Search ANY:')

    def update_search_mode(self, clickevent):
        if self.search_all.get():
            self.set_search_any()
        else:
            self.set_search_all()

    def print_q(self, *args):
        if self.entry_username.lb_exists:
            self.entry_username.select(None)
            self.entry_username.lb.destroy()
        self.quser.set(self.entry_username.get())

        state_val = self.filter_job_status.get()
        state_key = from_val(self.job_stati, state_val)

        partition_val = self.filter_partition.get()
        partition_key = from_val(self.partitions, partition_val)

        qhandler = Queue(self.ssh_client, user=self.quser.get(), filters={'state': state_key, 'partition': partition_key})

        self.qv.display_queue(qhandler, self.parent.queue_format.get().split())
        self.queue_visible.set(True)

    def execute_remote(self, cmd):
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        if not stderr.read():
            return stdout.read().decode('ascii')
        return None

    def monitor_running_pending_jobs(self):
        while True:
            try:
                qhandler = Queue(ssh_client=self.ssh_client, sftp_client=self.sftp_client, user=self.parent.user.get())
                q = qhandler.fetch()
                if q.empty:
                    return 0, 0
            except pmk.ssh_exception.SSHException:
                self.parent.login_window.authorize(self.parent.cluster.get())
                print('Reconnect to SSH')

            nrun = len(q.loc[q.state == 'RUNNING'].index)
            npen = len(q.loc[q.state == 'PENDING'].index)
            self.running_jobs.set(nrun)
            self.pending_jobs.set(npen)
            self.thread_job_alive.set(self.thread_jobs.is_alive())
            time.sleep(CONST_MONITOR_IDLE_TIME)

    def monitor_output_last_update(self):
        while True:
            pid = self.selected.get()
            qhandler = Queue(ssh_client=self.ssh_client, sftp_client=self.sftp_client, user=self.quser.get())
            job = qhandler.get_job(qhandler.fetch(), pid)
            timestamp = None

            if not job.empty:
                fname = str(job.outputfile.item())
                try:
                    self.sftp_client.stat(fname)
                    stdout = self.execute_remote(f'ls -ltr {fname}')
                    timestamp = " ".join(stdout.split()[5:8])
                except FileNotFoundError:
                    timestamp = 'File not found'
                except AmbiguousJobError:
                    timestamp = 'Ambiguous PID'
                except NotMatchedError:
                    timestamp = None

            self.timestamp.set(timestamp)
            time.sleep(CONST_MONITOR_IDLE_TIME*4)

    def quit(self):
        if messagebox.askyesno(self.parent.name, "Are you sure you want to quit?"):
            self.parent.destroy()

    def show_tooltip(self, wid):
        try:
            self.tooltip.set(self.parent.tooltips[wid])
        except KeyError:
            self.tooltip.set(self.parent.tooltips['?'])

        if wid is not None:
            self.label_tooltip.config(text=f'Tooltip: {self.tooltip.get()}')

    def hide_tooltip(self):
        self.tooltip.set(self.parent.tooltips['idle'])
        self.label_tooltip.config(text=f'Tooltip: {self.tooltip.get()}')

    def print_file_contents(self, ftype):
        qhandler = Queue(ssh_client=self.ssh_client, sftp_client=self.sftp_client, user=self.quser.get())

        pid = self.selected.get()
        if self.quser.get() != self.parent.user.get():
            return messagebox.showerror('Error', "You do not have permission to read another user's files.")
        elif not pid:
            return messagebox.showerror('Error', 'No PID selected.')

        if self.parent.open_in_separate_window.get():
            ExternalViewer(self, qhandler, pid, ftype, skip_to_end=True if ftype == 'output' else False)
        else:
            try:
                self.qv.display_file(qhandler, pid, ftype, skip_to_end=True if ftype == 'output' else False)
                self.queue_visible.set(False)
            except FileNotFoundError as e:
                tk.messagebox.showerror('Error', e)

    def setup_remote_connection(self):
        hostname = self.parent.hostnames[self.parent.cluster.get()]
        ssh_client = pmk.SSHClient()
        ssh_client.set_missing_host_key_policy(pmk.AutoAddPolicy())
        ssh_client.connect(username=self.parent.user.get(),
                           password=self.parent.pwd.get(),
                           hostname=hostname)

        transport = pmk.Transport((hostname, 22))
        transport.connect(None, self.parent.user.get(), self.parent.pwd.get())
        sftp_client = pmk.SFTPClient.from_transport(transport)
        return ssh_client, sftp_client

    def bind_events(self):
        self.parent.bind('<Shift-Return>', lambda event: self.print_q())
        self.parent.bind('<Control-plus>', lambda event: self.increase_fontsize())
        self.parent.bind('<Control-minus>', lambda event: self.decrease_fontsize())
        self.entry_username.bind('<Return>', self.print_q)
        self.entry_background_color.bind('<Return>', self.set_color)

    def launch_tutorial(self):
        return Tutorial(self)