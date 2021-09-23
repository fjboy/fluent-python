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


class DockerBuildException(Exception):
    pass


class DockerCmdException(Exception):
    pass


class DockerServiceException(Exception):
    pass


class DockerCmdDriver(object):

    @classmethod
    def build(cls, dockerfile, target):
        cmd = ['build', '-f', dockerfile, '-t', target, './']
        LOG.debug('build cmd: %s', ' '.join(cmd))
        return cls.execute(cmd)

    @classmethod
    def image_ls(cls):
        return cls.execute(['image', 'ls'])

    @classmethod
    def image_rm(cls, image):
        return cls.execute(['image', 'rm', image])

    @classmethod
    def image_inspect(cls, image, console=None):
        return cls.execute(['image', 'inspect', image], console=console)

    @classmethod
    def image_exists(cls, image):
        try:
            result = cls.image_inspect(image, console=False)
            return result.status == 0
        except DockerCmdException:
            return False

    @classmethod
    def rm(cls, name, force=False):
        cmd = ['rm', name]
        if force:
            cmd.append('--force')
        return cls.execute(cmd)

    @classmethod
    def stop(cls, name):
        return cls.execute(['stop', name])

    @classmethod
    def run(cls, image, name, volumes=None, privileged=False, network=None):
        cmd = ['run', '-itd', '--name={}'.format(name)]
        if privileged:
            cmd.append('--privileged=true')
        if network:
            cmd.append('--network={}'.format(network)),
        for volume in volumes or []:
            cmd.extend(['-v', volume])
        cmd.append(image)
        return cls.execute(cmd)

    @classmethod
    def execute(cls, cmd, console=None):
        stdout_file = None if VERBOSE \
            else os.path.join(PROJECT_PATH, 'deploy.log')
        cmd = ['docker'] + cmd
        result = LinuxExecutor.execute(
            cmd, stdout_file=stdout_file, stderr_file=stdout_file,
            console=console if console is not None else VERBOSE)
        if result.status != 0:
            LOG.error('stdout %s, stderr: %s', result.stdout, result.stderr)
            raise DockerCmdException(
                'run docker cmd failed, see detail {}'.format(stdout_file))
        return result


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

    @staticmethod
    def get_image(component):
        return '{}/{}'.format(CONF.docker.build_target, component)

    @staticmethod
    def get_volumes(component):
        option = '{}_volumes'.format(component.replace('-', '_'))
        try:
            volumes =  getattr(CONF.deploy, option)
        except:
            volumes = None
        LOG.info('xxx option: %s', option)
        LOG.info('xxx volumes: %s', volumes)
        LOG.info('xxx mariadb volumes: %s', CONF.deploy.mariadb_volumes)
        return volumes

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
            LOG.info('[%s] clean up tmp files', component)
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

    def start(self, component):
        volumes = self.get_volumes(component)
        DockerCmdDriver.run(self.get_image(component), component,
                            volumes=volumes,
                            privileged=True, network='host')

    def stop(self, component):
        DockerCmdDriver.stop(component)

    def cleanup(self, component):
        LOG.info('[%s] delete contrainer', component)
        try:
            DockerCmdDriver.rm(component)
        except:
            pass
        LOG.info('[%s] delete image', component)
        DockerCmdDriver.image_rm(self.get_image(component))

class DeploymentBase(object):
    
    def __init__(self, verbose=False):
        super(DeploymentBase, self).__init__()
        self.driver = DockerDeployDriver()
        global VERBOSE
        VERBOSE = verbose

    def get_hosts_config(self):
        component_host = CONF.deploy.component_host
        hosts_mapping = {}
        for component, hosts in CONF.deploy.components.items():
            if component in component_host:
                hosts_mapping[component_host[component]] = hosts.split(',')
        return hosts_mapping

    def deploy(self, component):
        if self.driver.is_deployed(component):
            LOG.warning('[%s] deployed, skip', component)
            return
        LOG.info('[%s] start to deploy', component)
        self.driver.deploy(component)

    def start(self, component):
        if not self.driver.is_deployed(component):
            LOG.error('[%s] is not depolyed', component)
            return
        LOG.info('[%s] starting', component)
        self.driver.start(component)

    def stop(self, component):
        if not self.driver.is_deployed(component):
            LOG.error('[%s] is not depolyed', component)
            return
        LOG.info('[%s] stoping', component)
        self.driver.stop(component)

    def cleanup(self,  component):
        if not self.driver.is_deployed(component):
            LOG.warning('[%s] is not depolyed', component)
            return
        LOG.info('[%s] cleanup', component)
        self.driver.cleanup(component)
