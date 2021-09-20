import os
from fplib.common import log
from fplib.executor import LinuxExecutor
import shutil

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = log.getLogger(__name__)


def get_env(name, default=None):
    return os.getenv(name, default)


class DockerBuildException(Exception):
    pass


class DockerCmdDriver(object):

    @classmethod
    def build(cls, dockerfile, target, verbose=False):
        cmd = ['docker', 'build', '-f', dockerfile, '-t', target, './']
        LOG.debug('build cmd: %s', ' '.join(cmd))
        stdout = None if verbose else os.path.join(PROJECT_PATH, 'deploy.log')
        result = LinuxExecutor.execute(cmd, console=verbose,
                                       stdout_file=stdout, stderr_file=stdout)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerBuildException(
                'build failed, see detail {}'.form(stdout))


class DockerDeployDriver(object):

    def __init__(self):
        self.resources_path = self.get_resources_dir()

    def get_resources_dir(self):
        project_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_path, 'resources')

    def deploy(self, component, verbose=False):
        if not get_env('DOCKER_FILE'):
            raise Exception('please source docker_openrc.sh first')
        dockerfile = get_env('DOCKER_FILE')
        target = '{}/{}'.format(get_env('DOCKER_BUILD_TARGET'), component)
        yum_repo = os.path.join(self.resources_path,
                                get_env('DOCKER_BUILD_YUM_REPO'))
        workspace = os.path.join(self.resources_path, 'mariadb')
        try:
            LOG.info('[%s] prepare resources', component)
            shutil.copy(yum_repo, workspace)
            os.chdir(workspace)
            LOG.info('[%s] build image start', component)
            DockerCmdDriver.build(dockerfile, target, verbose=verbose)
            LOG.info('[%s] build image success, target=%s', component, target)
        finally:
            LOG.info('[%s] clean up', component)
            self.cleanup_file(get_env('DOCKER_BUILD_YUM_REPO'))

    @classmethod
    def cleanup_file(cls, file_path):
        if os.path.isfile(file_path):
            os.remove(file_path)

    def current_dir(self):
        return os.getcwd()


class DeploymentBase(object):
    
    def __init__(self):
        super(DeploymentBase, self).__init__()
        self.driver = DockerDeployDriver()

    def deploy(self, component, verbose=False):
        LOG.info('[%s] start to deploy', component)
        self.driver.deploy(component, verbose=verbose)
