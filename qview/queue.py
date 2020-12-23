import pandas as pd
from collections import OrderedDict
from pathlib import Path
from exceptions import *


class Queue:
    def __init__(self, user, ssh_client, sftp_client=None, ext_input='.inp', ext_output='.out'):
        self.ssh_client = ssh_client
        self.sftp_client = sftp_client
        self.user = user
        self.ext_input = ext_input
        self.ext_output = ext_output
        self.scratch = '/cluster/work/jobs'

        self.field_width = 400
        self.fields = ['jobid', 'name', 'username', 'state', 'timeleft', 'submittime', 'timelimit', 'command',
                       'endtime', 'minmemory', 'mintime', 'nice', 'nodelist', 'numcpus', 'numnodes', 'numtasks',
                       'partition', 'priority', 'qos', 'state', 'starttime', 'stdin', 'stdout', 'stderr', 'submittime',
                       'timeleft', 'timeused', 'timelimit', 'userid', 'workdir']

        self.q = self.parse()

    def parse(self):
        fmt = [el+f':.{self.field_width}' for el in self.fields]
        cmd = f'squeue --noheader -u {self.user} -O {",".join(fmt)}'
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        raw = stdout.readlines()
        if not raw:
            return pd.DataFrame([], columns=self.fields)

        start = [i * self.field_width for i in range(len(self.fields))]
        stop = [(i+1)*self.field_width for i in range(len(self.fields))]

        q = []
        for job in raw:
            d = OrderedDict({})
            for s, e, key in zip(start, stop, self.fields):
                d[key] = job[s:e].strip()

            d['inputfile'] = Path(d['workdir']).joinpath(Path(d['stdout']).stem + self.ext_input)
            d['outputfile'] = Path(self.scratch).joinpath(d['jobid'], Path(d['stdout']).stem + self.ext_output)

            q.append(d)

        return pd.DataFrame.from_dict(q)

    def get_job(self, pid):
        job = self.q.loc[self.q.jobid == pid]
        if len(job.index) > 1:
            raise AmbiguousJobError('PID macthed more than one job')
        return self.q.loc[self.q.jobid == pid]

    def get_file_content(self, pid, ftype):
        job = self.get_job(pid)

        if ftype == 'input':
            fname = job.inputfile.item()
        elif ftype == 'output':
            fname = job.outputfile.item()
        elif ftype == 'error':
            fname = job.stderr.item()
        elif ftype == 'job':
            fname = job.command.item()

        with self.sftp_client.open(str(fname)) as f:
            content = f.read()

        return fname, content

    def filter(self, state='ALL'):
        if state == 'ALL':
            return self.q
        else:
            try:
                return self.q.loc[self.q.state == state]
            except:
                return self.q
