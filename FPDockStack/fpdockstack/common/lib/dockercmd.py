from fplib.common import log
from fplib.executor import LinuxExecutor

LOG = log.getLogger(__name__)


class DockerBuildException(Exception):
    pass


class DockerCmdException(Exception):
    pass


class DockerServiceException(Exception):
    pass


class DockerCmdClient(object):

    def __init__(self, verbose=False, stdout=None):
        self.verbose = verbose
        self.stdout = self.stdout or 'dockerclient.log'

    def build(self, dockerfile, target):
        cmd = ['build', '-f', dockerfile, '-t', target, './']
        LOG.debug('build cmd: %s', ' '.join(cmd))
        return self.execute(cmd)

    def image_ls(self):
        return self.execute(['image', 'ls'])

    def image_rm(self, image):
        return self.execute(['image', 'rm', image])

    def image_inspect(self, image, console=None):
        return self.execute(['image', 'inspect', image], console=console)

    def image_exists(self, image):
        try:
            result = self.image_inspect(image, console=False)
            return result.status == 0
        except DockerCmdException:
            return False

    def rm(self, name, force=False):
        cmd = ['rm', name]
        if force:
            cmd.append('--force')
        return self.execute(cmd)

    def stop(self, name):
        return self.execute(['stop', name])

    def run(self, image, name, volumes=None, privileged=False, network=None):
        cmd = ['run', '-itd', '--name={}'.format(name)]
        if privileged:
            cmd.append('--privileged=true')
        if network:
            cmd.append('--network={}'.format(network)),
        for volume in volumes or []:
            cmd.extend(['-v', volume])
        cmd.append(image)
        return self.execute(cmd)

    def execute(self, cmd, console=None):
        stdout_file = None if self.verbose else self.stdout
        cmd = ['docker'] + cmd
        result = LinuxExecutor.execute(
            cmd, stdout_file=stdout_file, stderr_file=stdout_file,
            console=console if console is not None else self.verbose)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerCmdException(
                'run docker cmd failed, see detail {}'.format(stdout_file))
        return result
