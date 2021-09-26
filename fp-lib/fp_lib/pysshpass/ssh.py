import getpass
import os

import paramiko

from fp_lib.common import log

LOG = log.getLogger(__name__)

DEFAULT_PORT = 22
DEFAULT_TIMEOUT = 60


class SSHOutput(object):

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return self.stderr.decode('utf-8') if self.stderr \
            else self.stdout.decode('utf-8')


class SSHRequest(object):

    def __init__(self, host, user=None, port=22, password=None, timeout=60):
        self.host = host
        self.user = user or getpass.getuser()
        self.port = port
        self.password = password
        self.timeout = timeout


class CmdRequest(SSHRequest):

    def __init__(self, cmd, *args, **kwargs):
        super(CmdRequest, self).__init__(*args, **kwargs)
        self.cmd = cmd


class ScpRequest(SSHRequest):

    def __init__(self, local, remote, *args, **kwargs):
        super(ScpRequest, self).__init__(*args, **kwargs)
        self.local = local or './'
        self.remote = remote or './'


class SSHClient(object):

    def __init__(self, host, user, password, port=None, timeout=None):
        self.host = host
        self.user = user
        self.password = password
        self.port = port or DEFAULT_PORT
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _connect(self):
        self.client.connect(hostname=self.host,
                            port=self.port,
                            username=self.user,
                            password=self.password,
                            timeout=self.timeout)

    def ssh(self, command, get_pty=False):
        self._connect()
        LOG.debug('execute: %s', command)
        result = self.client.exec_command(command, get_pty=get_pty)
        output = SSHOutput(result[1].read().strip(), result[2].read().strip())
        self.client.close()
        return output

    def get(self, remote_file, local_path='./'):
        if not os.path.exists(local_path):
            LOG.debug('make dirs: %s', local_path)
            os.makedirs(local_path)
        if os.path.isdir(local_path):
            save_path = os.path.join(local_path,
                                     os.path.basename(remote_file))
        else:
            save_path = local_path
        LOG.debug('get %s -> %s from %s', remote_file, save_path, self.host)
        self._connect()
        sftp = self.client.open_sftp()
        with open(save_path, 'wb') as f:
            sftp.getfo(remote_file, f)
        sftp.close()

    def put(self, local_file, remote_path='./'):
        if not os.path.exists(local_file):
            raise IOError('Error: local file {} not exists'.format(local_file))
        self._connect()
        sftp = self.client.open_sftp()
        try:
            sftp.listdir(remote_path)
            save_path = '/'.join([remote_path, os.path.basename(local_file)])
        except IOError:
            save_path = remote_path
        LOG.debug('put %s -> %s at %s', local_file, save_path, self.host)
        sftp.put(local_file, save_path)
        sftp.close()


def run_cmd_on_host(request):
    ssh_client = SSHClient(request.host, request.user, request.password,
                           port=request.port, timeout=request.timeout)
    return ssh_client.ssh(request.cmd)


def download_from_host(request):
    ssh_client = SSHClient(request.host, request.user, request.password,
                           port=request.port, timeout=request.timeout)
    ssh_client.get(request.remote, request.local)


def upload_to_host(request):
    ssh_client = SSHClient(request.host, request.user, request.password,
                           port=request.port, timeout=request.timeout)
    ssh_client.put(request.local, request.remote)
