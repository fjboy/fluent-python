import abc
import os
import shutil

from fplib.common import log
from fplib.executor import LinuxExecutor

from common import config

CONF = config.CONF

VERBOSE = False
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = log.getLogger(__name__)


def get_env(name, default=None):
    return os.getenv(name, default)


class DockerBuildException(Exception):
    pass


class DockerCmdException(Exception):
    pass


class DockerServiceException(Exception):
    pass


class DockerCmdDriver(object):

    @classmethod
    def build(cls, dockerfile, target):
        cmd = ['docker', 'build', '-f', dockerfile, '-t', target, './']
        LOG.debug('build cmd: %s', ' '.join(cmd))
        stdout = None if VERBOSE else os.path.join(PROJECT_PATH, 'deploy.log')
        result = LinuxExecutor.execute(cmd, console=VERBOSE,
                                       stdout_file=stdout, stderr_file=stdout)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerBuildException(
                'build failed, see detail {}'.format(stdout))

    @classmethod
    def image_ls(cls):
        cmd = ['docker', 'image', 'ls']
        stdout = None if VERBOSE else os.path.join(PROJECT_PATH, 'deploy.log')
        result = LinuxExecutor.execute(cmd, console=VERBOSE,
                                       stdout_file=stdout, stderr_file=stdout)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerCmdException(
                'list image failed, see detail {}'.format(stdout))

    @classmethod
    def image_inspect(cls, image):
        cmd = ['docker', 'image', 'inspect', image]
        stdout = None if VERBOSE else os.path.join(PROJECT_PATH, 'deploy.log')
        result = LinuxExecutor.execute(cmd, console=VERBOSE,
                                       stdout_file=stdout, stderr_file=stdout)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerCmdException(
                'list image failed, see detail {}'.format(stdout))

    @classmethod
    def image_exists(cls, image):
        cmd = ['docker', 'image', 'inspect', image]
        stdout = os.path.join(PROJECT_PATH, 'deploy.log')
        result = LinuxExecutor.execute(cmd, stdout_file=stdout,
                                        stderr_file=stdout)
        return result.status == 0



class DeployDriverBase(metaclass=abc.ABCMeta):

    def __init__(self, verbose=False):
        self.resources_path = self.get_resources_dir()
        self.components_path = self.get_components_dir()
        self.verbose = verbose
        self.enable = None

    @abc.abstractmethod
    def deploy(self, component):
        pass

    @abc.abstractmethod
    def is_deployed(self, component):
        pass

    def get_resources_dir(self):
        project_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_path, 'resources')

    def get_components_dir(self):
        project_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_path, 'components')


class DockerDeployDriver(DeployDriverBase):


    def deploy(self, component):
        if not self.is_enable():
            LOG.error('make sure docker service is started')
            return
        self.build(component)

    def build(self, component):
        dockerfile = CONF.docker.build_file
        yum_repo = os.path.join(PROJECT_PATH, 'resources',
                                CONF.docker.build_yum_repo)
        target = '{}/{}'.format(CONF.docker.build_target, component)
        workspace = os.path.join(self.components_path, component)
        LOG.info('[%s] prepare resources', component)
        shutil.copy(yum_repo, workspace)
        os.chdir(workspace)
        LOG.info('[%s] build image start', component)
        try:
            DockerCmdDriver.build(dockerfile, target)
            LOG.info('[%s] build image success, target=%s', component, target)
        finally:
            LOG.info('[%s] clean up', component)
            self.cleanup_file(CONF.docker.build_yum_repo)

    @classmethod
    def cleanup_file(cls, file_path):
        if os.path.isfile(file_path):
            os.remove(file_path)

    def current_dir(self):
        return os.getcwd()

    def is_enable(self):
        LOG.debug('enable %s', self.enable)
        if self.enable is None:
            try:
                DockerCmdDriver.image_ls()
                self.enable = True
            except DockerCmdException as e:
                self.enable = False
                LOG.error(e)
        return self.enable

    def is_deployed(self, component):
        target = '{}/{}'.format(CONF.docker.build_target, component)
        return DockerCmdDriver.image_exists(target)


class DeploymentBase(object):
    
    def __init__(self, verbose=False):
        super(DeploymentBase, self).__init__()
        self.driver = DockerDeployDriver()
        global VERBOSE
        VERBOSE = verbose

    def deploy(self, component):
        if self.driver.is_deployed(component):
            LOG.info('[%s] deployed', component)
            return
        LOG.info('[%s] start to deploy', component)
        self.driver.deploy(component)
