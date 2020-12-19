from pathlib import Path


class Job:
    def __init__(self, parent, pid):
        self.parent = parent
        self.pid = pid
        self.ssh_client = parent.ssh_client

        self.__dict__.update(self._parse_raw())

    def _parse_raw(self):
        jobinfo = {}
        for field in self.get_job_info().split():
            try:
                key, val = field.split('=')
                jobinfo[key.lower()] = val
            except ValueError:
                jobinfo[field] = None
        try:
            jobinfo['jobname'] = Path(jobinfo['stderr']).stem
        except KeyError:
            return {}
        return jobinfo

    def get_job_info(self):
        cmd = f'scontrol show jobid {self.pid} --oneliner'
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        return stdout.read().decode('ascii').lower()

    def find_inputfile(self):
        return Path(self.workdir).joinpath(self.jobname+'.inp')

    def find_outputfile(self):
        scratch = Path(self.parent.parent.scratch[self.parent.parent.cluster.get()]).joinpath(self.pid)
        return scratch.joinpath(self.jobname+'.out')

    def find_errorfile(self):
        return Path(self.stderr)

    def find_jobfile(self):
        return Path(self.command)

    def get_timestamp(self):
        try:
            cmd = f'ls -ltr {self.find_outputfile()} | awk \'{{print $6" "$7" "$8}}\''
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        except AttributeError:
            return 'Invalid PID'
        return stdout.read().decode('ascii').strip()
