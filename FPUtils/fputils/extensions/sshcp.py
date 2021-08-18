import os
import re
import socket
import paramiko
import time
from concurrent import futures

from fplib.common import cliparser
from fplib.common import log
from fplib.pysshpass import ssh

LOG = log.getLogger(__name__)

RE_CONNECTION = re.compile(r'((.*)@){0,1}([^:]+)(:(.*)){0,1}')
BASE_SSH_ARGUMENTS = [
    cliparser.Argument('-T', '--get_pty', action='store_true',
                       help='if set, use pty'),
    cliparser.Argument('-t', '--timeout', type=int,
                       help='Timeout of ssh, default is {}'.format(
                           ssh.DEFAULT_TIMEOUT)),
    cliparser.Argument('-P', '--port', type=int, default=22,
                       help='The port of SshServer, default is 22. It will be'
                            ' overwrited if set port=<PORT> in file.'),
    cliparser.Argument('-u', '--user',
                       help='The user for login, default is current user'),
    cliparser.Argument('-p', '--password', default='',
                       help='The password for login, default is "". It will be'
                            ' overwrited if set password=<PASSWORD> in file.'),
    cliparser.Argument('-w', '--worker', type=int,
                       help='Execute worker, use hosts num if not set'),
]


def is_support_tqdm():
    try:
        import tqdm                    # noqa
        return True
    except ImportError:
        LOG.warning('tqdm is not installed')
    return False


def parse_connect_info(connect_info):
    """
    Param:
        connection_info: e.g. root@localhost:/tmp
    Return:
        user, host, remote_path: e.g. root, localhost, /tmp
    """
    matched = RE_CONNECTION.match(connect_info)
    # NOTE: Example 'root@localhost:/tmp' will be parsed as
    # ('root@', 'root', 'localhost', ':/tmp', '/tmp')
    LOG.debug('regex match user=%s, host=%s, remote_path=%s',
              matched.group(2), matched.group(3), matched.group(5))
    return matched.group(2), matched.group(3), matched.group(5)


def parse_connect_info_from_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        columns = line.split()
        user, host, remote_path = parse_connect_info(columns[0])
        options = {}
        for col in columns[1:]:
            key, value = col.split('=')
            options[key] = value
        yield user, host, remote_path, options


def make_result(func):

    def wrapper(request, *args, **kwargs):
        try:
            output = func(request, *args, **kwargs)
        except socket.timeout:
            LOG.error('Connect to %s:%s timeout(%s seconds)',
                      request.host, request.port, request.timeout)
            output = 'ERROR: Connect timeout'
        except paramiko.ssh_exception.AuthenticationException:
            LOG.error('Authentication %s with "%s" failed',
                      request.user, request.password)
            output = 'ERROR: Auth failed, password is correct? (-p <PASSWORD>)'
        except Exception as e:
            LOG.error(e)
            output = e
        return {'host': request.host, 'output': output}

    return wrapper


def show_results(func):

    def wrapper(*args, **kwargs):
        start_time = time.time()
        results = func(*args, **kwargs)
        spend = time.time() - start_time
        for result in results:
            print('===== {} ====='.format(result.get('host')))
            print(result.get('output'))
        LOG.info('Spend %.2f seconds total', spend)

    return wrapper


@make_result
def run_cmd_on_host(cmd_request):
    LOG.debug('run cmd on host %s', cmd_request.host)
    return ssh.run_cmd_on_host(cmd_request)


@make_result
def download_from_host(scp_request):
    LOG.debug('run cmd on host %s', scp_request.host)
    ssh.download_from_host(scp_request)
    return 'success'


@make_result
def upload_to_host(scp_request):
    LOG.debug('upload to host %s', scp_request.host)
    ssh.upload_to_host(scp_request)
    return 'success'


@show_results
def run_cmd_on_hosts(cmd_requests, worker=None):
    worker = worker or len(cmd_requests)
    LOG.info('run cmd on %s hosts, worker is %s', len(cmd_requests), worker)
    results = []
    pbar = None
    if is_support_tqdm():
        from tqdm import tqdm
        pbar = tqdm(total=len(cmd_requests))
    with futures.ThreadPoolExecutor(worker) as executor:
        for result in executor.map(run_cmd_on_host, cmd_requests):
            results.append(result)
            if pbar:
                pbar.update(1)
    if pbar:
        pbar.close()
    return results


@show_results
def download_from_hosts(scp_requests, worker=None):
    worker = worker or len(scp_requests)
    LOG.info('download files from %s hosts, worker is %s',
             len(scp_requests), worker)
    results = []
    pbar = None
    if is_support_tqdm():
        from tqdm import tqdm
        pbar = tqdm(total=len(scp_requests))
    with futures.ThreadPoolExecutor(worker) as executor:
        for result in executor.map(download_from_host, scp_requests):
            results.append(result)
            if pbar:
                pbar.update(1)
    if pbar:
        pbar.close()
    return results


@show_results
def upload_to_hosts(scp_requests, worker=None):
    worker = worker or len(scp_requests)
    LOG.info('upload to %s hosts, worker is %s', len(scp_requests), worker)
    results = []
    pbar = None
    if is_support_tqdm():
        from tqdm import tqdm
        pbar = tqdm(total=len(scp_requests))
    with futures.ThreadPoolExecutor(worker) as executor:
        for result in executor.map(upload_to_host, scp_requests):
            results.append(result)
            if pbar:
                pbar.update(1)
    if pbar:
        pbar.close()
    return results


class SSHCmd(cliparser.CliBase):
    NAME = 'ssh-run'
    ARGUMENTS = [
        cliparser.Argument('host',
                           help='The host to connect, string or file. '
                                'String like: root@host1 , File like: '
                                'root@host1 port=80 password=PASSWORD'),
        cliparser.Argument('command', help='The command to execute')
    ] + BASE_SSH_ARGUMENTS

    def __call__(self, args):
        requests = []
        for user, host, _, opts in get_connect_info(args):
            req = ssh.CmdRequest(args.command, host,
                                 user=user or args.user,
                                 password=opts.get('password', args.password),
                                 port=opts.get('port', args.port),
                                 timeout=args.timeout)
            requests.append(req)

        run_cmd_on_hosts(requests, worker=args.worker)


def get_connect_info(args):
    if os.path.isfile(args.host):
        connect_info = parse_connect_info_from_file(args.host)
    else:
        user, host, remote_path = parse_connect_info(args.host)
        connect_info = [(user, host, remote_path, {})]
    return connect_info


class ScpGet(cliparser.CliBase):
    NAME = 'scp-get'
    ARGUMENTS = [
        cliparser.Argument('host',
                           help='The remote host to connect, string or file'),
        cliparser.Argument('--remote', help='Remote file path'),
        cliparser.Argument('--local', default='./',
                           help='The local path to save, defualt is ./ .')
    ] + BASE_SSH_ARGUMENTS

    def __call__(self, args):
        requests = []
        for user, host, remote_path, opts in get_connect_info(args):
            remote = remote_path or args.remote
            if not remote:
                LOG.error('remote_path is not set for host: %s', host)
                return 1
            local_path = os.path.join(args.local, host)
            req = ssh.ScpRequest(local_path, args.remote, host,
                                 user=user or args.user,
                                 password=opts.get('password', args.password),
                                 port=opts.get('port', args.port),
                                 timeout=args.timeout)
            requests.append(req)
        download_from_hosts(requests, worker=args.worker)


class ScpPut(cliparser.CliBase):
    NAME = 'scp-put'
    ARGUMENTS = [
        cliparser.Argument('local', help='The local path to put.'),
        cliparser.Argument('host',
                           help='The remote host to connect, string or file'),
        cliparser.Argument('--remote', default='./',
                           help='The remote path to save.'),
    ] + BASE_SSH_ARGUMENTS

    def __call__(self, args):
        if not os.path.exists(args.local):
            LOG.error('Local file %s not found', args.local)
            return
        requests = []
        for user, host, remote_path, opts in get_connect_info(args):
            remote_path = remote_path or args.remote
            req = ssh.ScpRequest(args.local, remote_path, host,
                                 user=user or args.user,
                                 password=opts.get('password', args.password),
                                 port=opts.get('port', args.port),
                                 timeout=args.timeout)
            requests.append(req)
        upload_to_hosts(requests, worker=args.worker)


def list_sub_commands():
    return [SSHCmd, ScpGet, ScpPut]
