import pandas as pd
from collections import OrderedDict
from pathlib import Path
from exceptions import *
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


class Queue:
    def __init__(self, ssh_client=None, sftp_client=None, user=None, filters=None, ext_input='.inp', ext_output='.out'):
        if filters is None:
            filters = {'state': 'ALL', 'partition': 'ALL'}
        self.ssh_client = ssh_client
        self.sftp_client = sftp_client
        self.ext_input = ext_input
        self.ext_output = ext_output
        self.user = user
        self.filters = filters
        self.scratch = '/cluster/work/jobs'

        self.field_width = 200
        self.headers = sorted(['jobid', 'name', 'username', 'userid', 'state', 'timelimit', 'timeleft',
                        'timeused', 'stdin', 'stdout', 'stderr', 'workdir', 'starttime', 'submittime', 'nice', 'priority',
                        'qos', 'partition', 'minmemory', 'numnodes', 'numcpus', 'numtasks', 'mintime', 'nodelist',
                        'reason', 'command', 'reasonlist', 'statecompact', 'endtime'])

    def fetch(self):
        fmt = [el+f':.{self.field_width}' for el in self.headers]
        if self.user == '' or self.user == 'all':
            cmd = f'squeue --noheader -O {",".join(fmt)}'
        else:
            cmd = f'squeue --noheader -u {self.user} -O {",".join(fmt)}'
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        raw = stdout.readlines()
        if not raw:
            return pd.DataFrame([], columns=self.headers)

        start = [i * self.field_width for i in range(len(self.headers))]
        stop = [(i+1)*self.field_width for i in range(len(self.headers))]

        q = []
        for job in raw:
            d = OrderedDict({})
            for s, e, key in zip(start, stop, self.headers):
                d[key] = job[s:e].strip()

            d['inputfile'] = Path(d['workdir']).joinpath(Path(d['stdout']).stem + self.ext_input)
            d['outputfile'] = Path(self.scratch).joinpath(d['jobid'], Path(d['stdout']).stem + self.ext_output)

            q.append(d)

        # Convert timelimit to hours
        queue = pd.DataFrame.from_dict(q).sort_values(by=['jobid'])

        timelimits = list(queue.timelimit)
        hours = []
        for tl in timelimits:
            d = self.parse_timelimit(tl)
            h = d['days']*24 + d['hours'] + d['minutes'] / 60 + d['seconds'] / 3600
            hours.append(h)
        hours = np.asarray(hours)
        cpus = np.asarray([int(el) for el in list(queue.numcpus)])
        queue['cpuhours'] = hours * cpus
        return self.filter_queue(queue.reset_index(), self.filters)

    def filter_queue(self, queue, filters):
        query = " & ".join([f'(@queue.{key} == "{val}")' for key, val in filters.items() if val != 'ALL'])
        if query == '':
            return queue
        else:
            return queue.query(query)

    def parse_timelimit(self, tl):
        try:
            days, rest = tl.split('-')
        except ValueError:
            days = 0
            rest = tl
        try:
            hours, minutes, seconds = rest.split(':')
        except ValueError:
            hours, minutes, seconds = 0, 0, 0

        return dict(days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds))
            

    def get_job(self, queue, pid):
        job = queue.loc[queue.jobid == pid]
        if len(job.index) > 1:
            raise AmbiguousJobError('PID matched more than one job')
        return queue.loc[queue.jobid == pid]

    def get_file_content(self, queue, pid, ftype):
        job = self.get_job(queue, pid)

        try:
            if ftype == 'input':
                fname = job.inputfile.item()
            elif ftype == 'output':
                fname = job.outputfile.item()
            elif ftype == 'error':
                fname = job.stderr.item()
            elif ftype == 'job':
                fname = job.command.item()
        except:
            raise FileNotFoundError(f'{ftype.upper()} file for pid={pid} not found.')

        with self.sftp_client.open(str(fname)) as f:
            content = f.read()

        return fname, content
