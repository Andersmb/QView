from job import Job


class Q:
    def __init__(self, parent, user=None):
        # Set up SSH client
        self.parent = parent
        self.ssh_client = self.parent.ssh_client
        self.user = user

    def fetch(self):
        if self.user:
            maxpid, maxname = self.longest_name()
            cmd = f'squeue -u {self.user} -S i -o \'%.{maxname+1}j %.{maxpid+1}i %.9P %.8T %.8u %.10M %.10l %.6D %R\''
        else:
            cmd = f'squeue -S i -o \'%.20j %.10i %.9P %.8T %.8u %.10M %.10l %.6D %R\''

        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        q = stdout.read().decode('ascii').split('\n')
        return q[:-1]

    def pids(self):
        cmd = f'squeue -u {self.user} -o \'%.40i\''
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        return [line.strip() for line in stdout.readlines()][1:]

    def longest_name(self):
        cmd = f'squeue -u {self.user} -o \'%.20i %.800j\''
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        q = stdout.readlines()
        pidlength = max([len(line.split()[0].strip()) for line in q])
        namelength = max([len(line.split()[1].strip()) for line in q])
        return pidlength, namelength

    def count_run_pend(self):
        n_pending = 0
        n_running = 0

        for pid in self.pids():
            job = Job(self.parent, pid)
            try:
                if job.jobstate.lower() == 'running':
                    n_running += 1
                elif job.jobstate.lower() == 'pending':
                    n_pending += 1
            except:
                pass
        return n_running, n_pending
