import abc
import os
import shutil
import docker
import requests
import json

from docker import client
from docker import errors

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

    def __init__(self, verbose=False):
        super().__init__(verbose=verbose)
        self.docker = client.DockerClient()

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
        return volumes

    def build(self, component):
        dockerfile = CONF.docker.build_file
        yum_repo = os.path.join(PROJECT_PATH, 'resources',
                                CONF.docker.build_yum_repo)
        tag = self.get_image(component)
        workspace = os.path.join(self.components_path, component)
        LOG.info('[%s] prepare resources', component)
        shutil.copy(yum_repo, workspace)
        LOG.info('[%s] building image', component)
        try:
            cli = docker.APIClient()
            for line in cli.build(path=workspace, dockerfile=dockerfile,
                                  tag=tag, rm=True):
                stream = json.loads(line).get('stream')
                if VERBOSE:
                    print(stream, end='')
                elif stream and stream.startswith('Step'):
                    LOG.info('[%s] %s', component, stream)
            LOG.info('[%s] build image success, tag=%s', component, tag)
        except Exception as e:
            LOG.error('[%s] build failed', component)
            LOG.exception(e)
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
        try:
            self.docker.version()
            return True
        except requests.exceptions.ConnectionError:
            return False

    def is_deployed(self, component):
        try:
            self.docker.images.get(self.get_image(component))
            return True
        except errors.ImageNotFound:
            return False

    def start(self, component):
        volumes = {}
        for volume in self.get_volumes(component):
            k, v = volume.split(':')
            volumes[v] = k
        LOG.info(volumes)
        try:
            container = self.docker.containers.get(component)
            if container.status != 'running':
                container.start()
            else:
                LOG.debug('[%s] status is %s', component, container.status)
        except errors.ContainerError:
            self.docker.containers.run(self.get_image(component),
                                    name=component,
                                    tty=True, detach=True, privileged=True,
                                    network='host', 
                                    volumes=volumes)

    def stop(self, component):
        container = self.docker.containers.get(component)
        container.stop()

    def cleanup(self, component):
        LOG.info('[%s] delete contrainer', component)
        try:
            container = self.docker.containers.get(component)
            container.remove()
        except errors.NotFound:
            pass
        try:
            self.docker.images.remove(self.get_image(component))
            LOG.info('[%s] delete image', component)
        except errors.ImageNotFound:
            pass


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
