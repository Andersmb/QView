import tkinter as tk
from tkinter import simpledialog, messagebox
import paramiko as pmk


class Login(tk.Frame):
    def __init__(self, parent, firstlogin, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.firstlogin = firstlogin

        self.create_widgets()

    def create_widgets(self):
        for i, cluster in enumerate(self.parent.hostnames.keys()):
            login_cmd = lambda cluster=cluster: self.authorize(cluster)
            tk.Button(self,
                      image=self.parent.images[cluster],
                      width=100,
                      height=100,
                      command=login_cmd,
                      highlightbackground='black',
                      highlightthickness=3).grid(row=0, column=i, padx=5, pady=5)
            tk.Label(self, text=cluster.upper()).grid(row=1, column=i, padx=5, pady=5)

    def authorize(self, cluster):
        self.parent.cluster.set(cluster)
        hostname = self.parent.hostnames[cluster]

        # Ask for login credentials if first login
        if self.firstlogin:
            user = simpledialog.askstring(self.parent.name, 'Username:')
            pwd = simpledialog.askstring(self.parent.name, 'Password:', show="*")

            try:
                self.send_credentials(user, pwd, hostname)
                self.parent.user.set(user)
                self.parent.pwd.set(pwd)
                self.parent.show_home()
                self.firstlogin = False

            except pmk.ssh_exception.AuthenticationException:
                messagebox.showerror(self.parent.name, 'Incorrect username or password. Please try again')

        else:
            try:
                self.send_credentials(self.parent.user.get(), self.parent.pwd.get(), hostname)
                self.parent.show_home()
            except:
                messagebox.showerror(self.parent.name, 'Login failed')
                raise pmk.ssh_exception.AuthenticationException('Login failed')

    def send_credentials(self, user, pwd, hostname):
        self.parent.ssh_client.connect(username=user, hostname=hostname, password=pwd)
