import tkinter as tk
from tkinter import messagebox
from datetime import datetime as dt, timedelta
import time
import paramiko as pmk
from threading import Thread

from q import Q
from job import Job
from custom_widgets import MyButton, MyLabel
from external_viewer import ExternalViewer

# Define some constants
CONST_HISTORY_LENGTH = 28  # How long back to look at job history
CONST_MONITOR_IDLE_TIME = 0.2  # For background monitoring


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
        self.selected = tk.StringVar()  # For monitoring the selected text
        self.selected.set('No job selected')
        self.running_jobs = tk.IntVar()  # For monitoring the number of running jobs
        self.running_jobs.set(0)
        self.pending_jobs = tk.IntVar()  # For monitoring the number of pending jobs
        self.pending_jobs.set(0)
        self.quser = tk.StringVar()
        self.quser.set(self.parent.user.get())
        self.thread_ssh_alive = tk.BooleanVar()
        self.thread_job_alive = tk.BooleanVar()
        self.thread_sel_alive = tk.BooleanVar()
        self.monitor_hostname = tk.StringVar()  # For displaying current hostname in status panel
        self.monitor_hostname.set(self.parent.hostnames[self.parent.cluster.get()])
        self.search_all = tk.BooleanVar()
        self.search_all.set(0)
        self.tooltip = tk.StringVar()
        self.tooltip.set(self.parent.tooltips['idle'])
        self.timestamp = tk.StringVar()

        # Define the job history length and set default to today
        self.job_history = [dt.today().date() - timedelta(days=i) for i in range(CONST_HISTORY_LENGTH)]
        self.parent.job_history_startdate.set(str(dt.today().date()))

        # Define the job status variables and set default to all jobs
        self.job_status = tk.StringVar()
        self.job_stati = {'A': 'All jobs', 'R': 'Running', 'PD': 'Pending', 'CD': 'Completed', 'TO': 'Timeout'}
        self.job_status.set(self.job_stati['A'])

        # Create the widgets
        self.create_widgets()

        # Start threads for background monitoring
        self.thread_jobs = Thread(target=self.monitor_running_pending_jobs, daemon=True)
        self.thread_selected = Thread(target=self.monitor_selected_text, daemon=True)
        self.thread_timestamp = Thread(target=self.monitor_output_last_update, daemon=True)

        self.thread_jobs.start()
        self.thread_selected.start()
        self.thread_timestamp.start()

        # Bind events to Home
        self.bind_events()

        # Configure queue window tags for color syntax
        self.configure_tags()

        # Print the queue
        self.print_q()

    def create_widgets(self):
        self.grid(row=0, column=0, sticky=tk.NSEW)
        pads_inner = dict(padx=0, pady=1)
        pads_outer = dict(padx=5, pady=5)

        # Define frames for holding widgets
        self.frame_top = tk.Frame(self)
        self.frame_top.grid(row=0, column=0, sticky=tk.NSEW)

        self.frame_toptools = tk.Frame(self.frame_top, highlightbackground="black", highlightthickness=2)
        self.frame_visualization = tk.Frame(self.frame_top, highlightbackground="black", highlightthickness=2)
        self.frame_filters = tk.Frame(self.frame_top, highlightbackground="black", highlightthickness=2)
        self.frame_status = tk.Frame(self.frame_top, highlightbackground="black", highlightthickness=2)
        self.frame_cluster = tk.Frame(self.frame_top, highlightbackground="black", highlightthickness=2)
        self.frame_prefs = tk.Frame(self.frame_top, highlightbackground='black', highlightthickness=2)
        self.frame_q = tk.Frame(self, width=1000, height=300)
        self.frame_q.grid_propagate(False)
        self.frame_q.grid_rowconfigure(0, weight=1)
        self.frame_q.grid_columnconfigure(0, weight=1)
        self.frame_bottools = tk.Frame(self, highlightbackground='black', highlightthickness=2)

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
        MyButton(self.frame_toptools, 'button_print_q', image=self.parent.images['cow'], width=60, height=60, command=self.print_q).grid(row=1, column=0, columnspan=2, **pads_inner)
        MyButton(self.frame_toptools, 'button_input', image=self.parent.images['icon_input'], width=30, height=30, command=self.print_inputfile).grid(row=2, column=0, **pads_inner)
        MyButton(self.frame_toptools, 'button_output', image=self.parent.images['icon_output'], width=30, height=30, command=self.print_outputfile).grid(row=2, column=1, **pads_inner)
        MyButton(self.frame_toptools, 'button_error', image=self.parent.images['icon_error'], width=30, height=30, command=self.print_errorfile).grid(row=3, column=0, **pads_inner)
        MyButton(self.frame_toptools, 'button_job', image=self.parent.images['icon_job'], width=30, height=30, command=self.print_jobfile).grid(row=3, column=1, **pads_inner)
        MyButton(self.frame_toptools, 'button_history', image=self.parent.images['icon_history'], width=30, height=30, command=self.notimplemented).grid(row=4, column=0, pady=2, padx=2)
        MyButton(self.frame_toptools, 'button_cost', image=self.parent.images['icon_cost'], width=30, height=30, command=self.notimplemented).grid(row=4, column=1, **pads_inner)
        MyButton(self.frame_toptools, 'button_cpu', image=self.parent.images['icon_cpu'], width=30, height=30, command=self.notimplemented).grid(row=5, column=0, **pads_inner)

        MyLabel(self.frame_visualization, 'label_visualization', text="VISUALS").grid(row=0, column=0, pady=5, padx=5)
        MyButton(self.frame_visualization, 'button_scfconv', image=self.parent.images['icon_scfconv'], width=50, height=50, command=self.notimplemented).grid(row=1, column=0, **pads_inner)
        MyButton(self.frame_visualization, 'button_geomconv', image=self.parent.images['icon_geomconv'], width=50, height=50, command=self.notimplemented).grid(row=2, column=0, **pads_inner)
        MyButton(self.frame_visualization, 'button_avogadro', image=self.parent.images['icon_avogadro'], width=50, height=50, command=self.notimplemented,
                  highlightbackground='black', highlightthickness=1).grid(row=3, column=0, **pads_inner)

        MyLabel(self.frame_filters, 'label_filters', text="FILTERS").grid(row=0, column=0, columnspan=2, **pads_outer)
        MyLabel(self.frame_filters, 'label_username', text='Username:').grid(row=1, column=0, sticky=tk.W, **pads_inner)
        self.entry_username = tk.Entry(self.frame_filters, width=10)
        self.entry_username.grid(row=1, column=1, sticky=tk.W, **pads_inner)
        self.entry_username.insert(0, self.parent.user.get())

        MyLabel(self.frame_filters, 'label_jobstatus', text='Job status:').grid(row=2, column=0, sticky=tk.W, **pads_inner)
        tk.OptionMenu(self.frame_filters, self.job_status, *[self.job_stati[s] for s in self.job_stati]).grid(row=2, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_filters, 'label_submitdate', text='Submit date:').grid(row=3, column=0, sticky=tk.W, **pads_inner)
        tk.OptionMenu(self.frame_filters, self.parent.job_history_startdate, *self.job_history).grid(row=3, column=1, sticky=tk.W, **pads_inner)

        self.label_search = MyLabel(self.frame_filters, 'label_search', text='Search ANY:')
        self.label_search.grid(row=4, column=0, sticky=tk.W, **pads_inner)
        self.label_search.bind('<Button-1>', self.update_search_mode)
        self.entry_search = tk.Entry(self.frame_filters, width=10)
        self.entry_search.grid(row=4, column=1, sticky=tk.W, **pads_inner)

        MyLabel(self.frame_status, 'label_status', text="STATUS").grid(row=0, column=0, columnspan=2, **pads_outer)
        MyLabel(self.frame_status, 'label_hostname', text="Hostname:").grid(row=1, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.monitor_hostname).grid(row=1, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_selected', text="Selected:").grid(row=2, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.selected).grid(row=2, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_running', text="Running jobs:").grid(row=3, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.running_jobs).grid(row=3, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_pending', text="Pending jobs:").grid(row=4, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.pending_jobs).grid(row=4, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_jobworker', text='Job worker:').grid(row=5, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.thread_job_alive).grid(row=5, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_selworker', text='SEL worker:').grid(row=6, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.thread_sel_alive).grid(row=6, column=1, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, 'label_timestamp', text='Last update:').grid(row=7, column=0, sticky=tk.W, **pads_inner)
        MyLabel(self.frame_status, None, textvar=self.timestamp).grid(row=7, column=1, sticky=tk.W, **pads_inner)

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
        MyLabel(self.frame_prefs, 'label_fontsize', text='Queue fontsize:').grid(row=1, column=0, **pads_inner)
        MyButton(self.frame_prefs, 'button_increasefont', image=self.parent.images['icon_+'], width=15, height=15, command=self.increase_fontsize).grid(row=1, column=1, **pads_inner)
        MyButton(self.frame_prefs, 'button_decreasefont', image=self.parent.images['icon_-'], width=15, height=15, command=self.decrease_fontsize).grid(row=1, column=2, **pads_inner)

        tk.Checkbutton(self.frame_prefs, text='External viewer', variable=self.parent.open_in_separate_window).grid(row=2, column=0, sticky=tk.W ,**pads_inner)

        MyButton(self.frame_prefs, 'button_savepref', text='Save', command=self.parent.dump_prefs).grid(row=99, column=0, sticky=tk.W, **pads_inner)

        # Main queue Text widget
        self.qwin = tk.Text(self.frame_q, wrap=tk.NONE, bg='black', fg='white', relief=tk.SUNKEN)
        self.qwin.grid(row=0, column=0, sticky=tk.NSEW)
        self.qwin.configure(font=self.parent.font_q)

        # Bottom tools
        MyButton(self.frame_bottools, 'button_quit', image=self.parent.images['icon_skull'], command=self.quit,
                 width=30, height=30).grid(row=0, column=0, sticky=tk.W, **pads_outer)
        MyButton(self.frame_bottools, 'button_toolbox', image=self.parent.images['icon_toolbox'],
                 command=self.notimplemented, width=30, height=30, highlightcolor='black', highlightthickness=1).grid(row=0, column=1, sticky=tk.W, **pads_outer)
        self.label_tooltip = tk.Label(self.frame_bottools, text=f'ToolTip: {self.tooltip.get()}', bg='#1f4a46', fg='#ffffff')
        self.label_tooltip.grid(row=0, column=99, **pads_outer)

    def increase_fontsize(self):
        s = self.parent.font_q.actual()['size'] + 2
        self.parent.font_q.configure(size=s)

    def decrease_fontsize(self):
        s = self.parent.font_q.actual()['size'] - 2
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
        self.qwin.delete('1.0', tk.END)
        self.quser.set(self.entry_username.get().strip())

        q = Q(parent=self, user=self.quser.get()).fetch()

        for i, line in enumerate(q):
            jobstate = line.split()[3].lower()
            self.qwin.insert(tk.END, line+'\n')
            self.qwin.tag_add(jobstate, f"{i+1}.0", f"{i+1}.{tk.END}")
            i += 1

    def execute_remote(self, cmd):
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        if not stderr.read():
            return stdout.read().decode('ascii')
        return None

    def monitor_running_pending_jobs(self):
        while True:
            nr, np = Q(parent=self, user=self.parent.user.get()).count_run_pend()
            self.running_jobs.set(nr)
            self.pending_jobs.set(np)
            self.thread_job_alive.set(self.thread_jobs.is_alive())
            time.sleep(CONST_MONITOR_IDLE_TIME)

    def monitor_selected_text(self):
        while True:
            s = self.select_text()
            if s and s != self.selected.get():
                self.selected.set(s)
            self.thread_sel_alive.set(self.thread_selected.is_alive())
            time.sleep(CONST_MONITOR_IDLE_TIME)

    def monitor_output_last_update(self):
        while True:
            pid = self.selected.get()
            timestamp = Job(self, pid).get_timestamp()
            self.timestamp.set(timestamp)
            time.sleep(CONST_MONITOR_IDLE_TIME*4)

    def select_text(self):
        try:
            s = int(self.qwin.get(tk.SEL_FIRST, tk.SEL_LAST))
            return s
        except:
            return ''

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

    def print_inputfile(self, *args):
        if self.quser.get() != self.parent.user.get():
            return messagebox.showerror('Error', "You don't have permission to do this.")

        job = Job(self, self.selected.get())
        try:
            inputfile = job.find_inputfile()
            with self.sftp_client.open(str(inputfile)) as f:
                content = f.read()
        except:
            messagebox.showerror('Error', 'Could not open input file')

        if self.parent.open_in_separate_window.get():
            return ExternalViewer(self, content)
        else:
            self.qwin.delete(0.1, tk.END)
            self.qwin.insert(tk.END, content)

    def print_jobfile(self, *args):
        if self.quser.get() != self.parent.user.get():
            return messagebox.showerror('Error', "You don't have permission to do this.")

        job = Job(self, self.selected.get())
        try:
            jobfile = job.find_jobfile()
            with self.sftp_client.open(str(jobfile)) as f:
                content = f.read()
        except:
            messagebox.showerror('Error', 'Could not open job file')

        if self.parent.open_in_separate_window.get():
            return ExternalViewer(self, content)
        else:
            self.qwin.delete(0.1, tk.END)
            self.qwin.insert(tk.END, content)

    def print_errorfile(self, *args):
        if self.quser.get() != self.parent.user.get():
            return messagebox.showerror('Error', "You don't have permission to do this.")

        job = Job(self, self.selected.get())
        try:
            errorfile = job.find_errorfile()
            with self.sftp_client.open(str(errorfile)) as f:
                content = f.read()
        except:
            messagebox.showerror('Error', 'Could not open error file')

        if self.parent.open_in_separate_window.get():
            return ExternalViewer(self, content)
        else:
            self.qwin.delete(0.1, tk.END)
            self.qwin.insert(tk.END, content)

    def print_outputfile(self, *args):
        if self.quser.get() != self.parent.user.get():
            return messagebox.showerror('Error', "You don't have permission to do this.")

        job = Job(self, self.selected.get())
        try:
            outputfile = job.find_outputfile()
            with self.sftp_client.open(str(outputfile)) as f:
                content = f.read()
        except:
            return messagebox.showerror('Error', 'Could not open output file')

        if self.parent.open_in_separate_window.get():
            return ExternalViewer(self, content, skip_to_end=True)
        else:
            self.qwin.delete(0.1, tk.END)
            self.qwin.insert(tk.END, content)
            self.qwin.see("end")

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

    def configure_tags(self):
        tag_colors = {
            'completed': '#717feb',
            'running': '#51c280',
            'pending': '#deb23a',
            'cancelled': '#d966d9',
            'timeout': '#de5f74'
        }
        for status, color in tag_colors.items():
            self.qwin.tag_configure(status, foreground=color)
        self.qwin.tag_raise(tk.SEL)