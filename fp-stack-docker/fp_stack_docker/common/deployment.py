import abc
import os
import socket
import shutil
import requests

from docker import client
from docker import errors
from fp_lib.common import log
from common import config
from common import exceptions
from common.docker import components

CONF = config.CONF
LOG = log.getLogger(__name__)


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
    COMPONENTS = components.list_all()

    def __init__(self, verbose=False):
        super().__init__(verbose=verbose)
        self.docker = client.DockerClient()
        self.components = {c.NAME: c for c in self.COMPONENTS}

    def get_component(self, name):
        if not name in self.components:
            raise exceptions.UnknownComponent(component=name)
        return self.components.get(name)()

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
        dc = self.get_component(component)
        yum_repo = os.path.join(self.get_resources_dir(),
                                CONF.docker.build_yum_repo)
        workspace = os.path.join(self.components_path, component)
        LOG.info('[%s] prepare resources', component)
        shutil.copy(yum_repo, workspace)
        LOG.info('[%s] building image', component)
        try:
            dc.build(workspace)
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
        dc = self.get_component(component)
        return dc.exists()

    def is_running(self, component):
        dc = self.get_component(component)
        return dc.running()

    def start(self, component):
        dc = self.get_component(component)
        try:
            dc.start()
        except exceptions.ComponentStarted:
            LOG.warning('[%s] is already started', component)
        except errors.ContainerError:
            LOG.info('[%s] creating', component)
            dc.run()
        LOG.info('[%s] started', component)

    def stop(self, component):
        dc = self.get_component(component)
        dc.stop()
        LOG.info('[%s] stopped', component)

    def cleanup(self, component, force=False):
        dc = self.get_component(component)
        if dc.running() and not force:
            LOG.error('[%s] is running, stop it first', component)
            return
        LOG.info('[%s] deleting', component)
        dc.remove(also_image=True)

    def get_status(self, component):
        dc = self.get_component(component)
        return dc.status()


class DeploymentBase(object):

    def __init__(self, verbose=False):
        super(DeploymentBase, self).__init__()
        self.driver = DockerDeployDriver()

    def get_hosts_config(self):
        component_host = CONF.deploy.component_host
        hosts_mapping = {}
        for component, hosts in CONF.deploy.components.items():
            if component in component_host:
                hosts_mapping[component_host[component]] = hosts.split(',')
        return hosts_mapping

    def deploy(self, component, force=False):
        if not force and self.driver.is_deployed(component):
            LOG.warning('[%s] deployed, skip', component)
            return

        LOG.info('[%s] start to deploy', component)
        self.driver.deploy(component)

    def update_hosts(self, component):
        LOG.info('update hosts for %s', component)
        component_host = self.get_component_host(component)
        if not component_host:
            return
        update_content = None
        component_ip = self.get_component_ip(component)
        with open('/etc/hosts', 'r') as f:
            lines = f.readlines()

        for line in lines:
            if line.strip().startswith(component_ip):
                return
        else:
            update_content = '{} {}\n'.format(component_ip, component_host)

        if not update_content:
            return
        with open('/etc/hosts', 'a+') as f:
            f.write(update_content)

    def get_component_host(self, component):
        hosts = {
            'keystone': 'keystone-server',
            'nova-api': 'nova-server',
            'glance-api': 'glance-server',
            'cinder-api': 'cinder-server',
            'neutron-server': 'neutron-server',
            'nova-api': 'nova-server',
        }
        return hosts.get(component)

    def get_component_ip(self, component):
        component_ip = None
        for c, hosts in CONF.deploy.components.items():
            if c != component:
                continue
            host_list = hosts.split(',')
            if len(host_list) == 1:
                component_ip = socket.gethostbyname(host_list[0])
                break
            component_ip = self.get_componet_vip(component)
            break
        if not component_ip:
            raise Exception('vip for {} is not config'.format(component))
        LOG.debug('%s ip is %s', component, component_ip)
        return component_ip

    def get_componet_vip(self, component):
        if not CONF.deploy.vip_mpping:
            raise Exception('vip_mapping is not set')
        return CONF.deploy.vip_mapping.get(component)

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
        if not self.driver.is_running(component):
            LOG.info('[%-20s] not running', component)
            return
        LOG.info('[%s] stoping', component)
        self.driver.stop(component)

    def cleanup(self,  component, force=False):
        if not self.driver.is_deployed(component):
            LOG.warning('[%s] is not depolyed', component)
            return
        LOG.info('[%s] cleanup', component)
        self.driver.cleanup(component, force=force)

    def status(self, component):
        """get component status

        Args:
            component (string): component name

        Returns:
            tuple: (installed, status)
        """
        installed = self.driver.is_deployed(component)
        status = installed and self.driver.get_status(component) or None
        return installed, status

    def config(self):
        pass
