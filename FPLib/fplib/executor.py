import sys
import locale
import subprocess
from collections import namedtuple

from fplib.common import log
LOG = log.getLogger(__name__)

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
    def execute(cmd, stdout_file=None, stderr_file=None, console=False):
        """ execute linux command
        e.g.
        >>> LinuxExecutor.execute('ls -l')
        """

        if stdout_file and isinstance(stdout_file, str):
            cmd.append('1>>{0}'.format(stdout_file))
        if stderr_file and isinstance(stderr_file, str):
            cmd.append('2>>{0}'.format(stderr_file))

        if print_console:
            stdout, stderr = sys.stdout, sys.stderr
        else:
            stdout, stderr = subprocess.PIPE, subprocess.PIPE

        LOG.debug('Execute: %s', ' '.join(cmd))
        p = subprocess.Popen(' '.join(cmd), shell=True,
                             stdout=stdout, stderr=stderr)
        out = read_stream(p.stdout)
        err = read_stream(p.stderr)
        p.communicate()
        LOG.debug('Stdout: %s, Stderr: %s', out, err)
        return ExecuteResult(p.returncode, ''.join(out), ''.join(err))
