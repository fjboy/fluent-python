import locale
import logging
import subprocess
from collections import namedtuple

LOG = logging.getLogger(__name__)

ExecuteResult = namedtuple('ExecutorResult', 'status stdout stderr')


def read_stream(stream):
    if not stream:
        return ''
    lines = []
    line = stream.readline()
    while line:
        lines.append(str(line, locale.getpreferredencoding()))
        line = stream.readline()
    return ''.join(lines)


class LinuxExecutor(object):

    @staticmethod
    def execute(cmd, stdout_file=None, stderr_file=None):

        if isinstance(stdout_file, str):
            cmd.append('1>{0}'.format(stdout_file))
        if isinstance(stderr_file, str):
            cmd.extend('2>{0}'.format(stderr_file))

        LOG.debug('Execute: %s', cmd)
        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = read_stream(p.stdout)
        err = read_stream(p.stderr)
        p.communicate()
        LOG.debug('Stdout: %s, Stderr: %s', out, err)
        return ExecuteResult(p.returncode, ''.join(out), ''.join(err))
