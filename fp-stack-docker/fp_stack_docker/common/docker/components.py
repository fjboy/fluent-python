from logging import addLevelName
import docker
import json
import socket

from docker import client
from docker import errors

from fp_lib.common import log
from common import config
from common import exceptions

CONF = config.CONF

LOG = log.getLogger(__name__)

COMPONENT_DRIVERS = None


class DockerComponent(object):
    NAME = 'DockerComponent'
    VOLUMES = {}
    NETWORK = 'host'

    def __init__(self):
        self.tag = '{}/{}'.format(CONF.docker.build_target, self.NAME)
        self.docker = docker.DockerClient()

    @property
    def image_name(self):
        return self.tag

    def deploy(self, component):
        if self.is_deployed(component):
            LOG.warning('[%s] deployed, skip', component)
            return
        LOG.info('[%s] start to deploy', component)
        self.driver.deploy(component)

    def build(self, path):
        cli = docker.APIClient()
        for line in cli.build(path=path, dockerfile=CONF.docker.build_file,
                              tag=self.tag, rm=True):
            stream = json.loads(line).get('stream')
            if CONF.verbose:
                print(stream, end='')
            elif stream and stream.startswith('Step'):
                LOG.info('[%s] %s', self.NAME, stream)
        
        if self.exists():
            LOG.debug('[%s] build image success, tag=%s', self.NAME, self.tag)
        else:
            LOG.error('[%s] build image failed', self.NAME)

    def start(self):
        if self.running():
            return
        try:
            container = self.docker.containers.get(self.NAME)
            if container.status != 'running':
                container.start()
        except errors.NotFound:
            LOG.debug('[%s] container not found, creating and run', self.NAME)
            self.run()

    def stop(self):
        container = self.docker.containers.get(self.NAME)
        container.stop()

    def run(self):
        cli = client.DockerClient()
        cli.containers.run(self.tag, name=self.NAME,
                           tty=True, detach=True, privileged=True,
                           network=self.NETWORK, volumes=self.VOLUMES,
                           command=self.get_command())

    def get_command(self):
        return None

    def remove(self, also_image=False):
        cli = client.DockerClient()
        try:
            container = cli.containers.get(self.NAME)
            LOG.debug('removing container %s', self.NAME)
            container.remove()
        except errors.NotFound:
            pass
        if also_image:
            try:
                LOG.debug('removing image %s', self.tag)
                cli.images.remove(self.tag)
            except errors.ImageNotFound:
                pass

    def exists(self):
        cli = client.DockerClient()
        try:
            cli.images.get(self.tag)
            return True
        except errors.ImageNotFound:
            return False

    def stared(self):
        cli = client.DockerClient()
        try:
            cli.containers.get(self.name)
            return True
        except errors.NotFound:
            return False

    def running(self):
        try:
            container = self.docker.containers.get(self.NAME)
            return container.status == 'running'
        except errors.NotFound:
            return False

    def status(self):
        try:
            container = self.docker.containers.get(self.NAME)
            return container.status
        except errors.NotFound:
            return None

    def config(self):
        LOG.info('[%s] config', self.NAME)
        if not self.running():
            LOG.error('%s is not running, can not config', self.NAME)
            return
        self._config()

    def _config(self):
        LOG.info('[%s] no config to do', self.NAME)

    def get_db_password(self, db):
        return CONF.openstack.db_identity.get(db, '')

    def get_auth_password(self, component):
        return CONF.openstack.auth_identity.get(component, '')

    def get_component_host(self, component):
        return CONF.deploy.components.get(component, '')

    def run_cmd_in_container(self, cmd, container=None):
        if not container:
            container = self.docker.containers.get(self.NAME)
        LOG.debug('RUN CMD: %s', cmd)
        output = container.exec_run(cmd)
        LOG.debug('RESULT : %s', output)
        return output


class Mariadb(DockerComponent):
    NAME = 'mariadb'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/var/log/mariadb': '/var/log/mariadb'}
    SQL_CREATE_DB = 'CREATE DATABASE IF NOT EXISTS {} ' \
                    'DEFAULT CHARACTER SET UTF8;'
    SQL_GRANT_LOCALHOST = "GRANT ALL PRIVILEGES ON {}.* TO '{}'@'localhost' " \
                          "IDENTIFIED BY '{}' with grant option;"
    SQL_GRANT_ALL = "GRANT ALL PRIVILEGES ON {}.* TO '{}'@'%' IDENTIFIED " \
                    "BY '{}' with grant option;"

    def _config(self):
        for component, _ in CONF.deploy.components.items():
            if component == 'keystone':
                self.init_database('keystone')
            elif component == 'neutron-server':
                self.init_database('neutron')
            elif component == 'nova-api':
                self.init_database('nova')
                self.init_database('nova_api')
            if component == 'glance-api':
                self.init_database('glance')
            if component == 'cinder-api':
                self.init_database('cinder')

    def init_database(self, database):
        LOG.info('[%s] init databse %s', self.NAME, database)
        container = self.docker.containers.get(self.NAME)
        result = self.run_cmd_in_container(self.SQL_CREATE_DB.format(database),
                                           container=container)
        if result:
            raise Exception('create database failed {}'.format(result))
        result = self.run_cmd_in_container(self.SQL_CREATE_DB.format(database),
                                           container=container)
        if result:
            raise Exception('create database failed {}'.format(result))
        password = self.get_db_password(database)

        LOG.info('[%s] grant for %s', self.NAME, database)
        self.run_sql_in_container(
            self.SQL_GRANT_LOCALHOST.format(database, database, password),
            container=container)
        self.run_sql_in_container(
            self.SQL_GRANT_ALL.format(database, database, password),
            container=container)
        self.run_sql_in_container('FLUSH PRIVILEGES;', container=container)

    def run_sql_in_container(self, sql, container):
        self.run_cmd_in_container(['mysql', '-uroot', '-e', sql],
                                  container=container)


class Memcached(DockerComponent):
    NAME = 'memcached'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/var/log/mariadb': '/var/log/mariadb'}

    def get_command(self):
        address = CONF.memcached.address
        if not address:
            addr = socket.getaddrinfo(socket.gethostname(), 'http')
            address = addr[0][4][0]
        return [
            '-p', str(CONF.memcached.port),
            '-u', CONF.memcached.user,
            '-m', str(CONF.memcached.maxcache),
            '-c', str(CONF.memcached.maxconn),
            '-l', address]


class Rabbitmq(DockerComponent):
    NAME = 'rabbitmq'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/var/log/mariadb': '/var/log/mariadb'}

    def _config(self):
        container = self.docker.containers.get(self.NAME)
        ip = CONF.rabbitmq.rabbitmq_node_ip
        if not ip:
            addr = socket.getaddrinfo(socket.gethostname(), 'http')
            ip = addr[0][4][0]
        container.exec_run(['echo', 'RABBITMQ_NODE_IP_ADDRESS={}'.format(ip),
                            '>>', '/etc/rabbitmq/rabbitmq-env.conf'])


class Keystone(DockerComponent):
    NAME = 'keystone'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/keystone': '/var/log/keystone',
               '/var/log/httpd': '/var/log/httpd'}

    def _config(self):
        container = self.docker.containers.get(self.NAME)
        pwd = self.get_db_password(self.NAME)
        host = self.get_component_host(self.NAME)
        cmd = [
            'openstack-config', '--set', '/etc/keystone/keystone.conf',
            'database',  'connection',
            'mysql+pymysql://keystone:{}@{}/keystone'.format(pwd, host)
        ]
        result = self.run_cmd_in_container(cmd, container=container)
        if result:
            raise Exception(
                'update keystone.conf failed, errror=%s'.format(result))

        result = self.run_cmd_in_container(cmd, container=container)
        if result:
            raise Exception(
                'update keystone.conf failed, errror=%s'.format(result))

        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container(['keystone-manage', 'db_sync'],
                                           container=container)
        if result:
            raise Exception('db sync failed, errror={}'.format(result))

        LOG.info('[%s] create endpoints', self.NAME)
        cmd = ['keystone-manage', 'bootstrap', '--bootstrap-password',
             self.get_auth_password(self.NAME),
             '--bootstrap-admin-url', 'http://keystone-server:35357/v3/',
             '--bootstrap-internal-url', 'http://keystone-server:35357/v3/',
             '--bootstrap-public-url', 'http://kestone-server:5000/v3/',
             '--bootstrap-region-id', 'RegionOne']
        result = self.run_cmd_in_container(cmd, container=container)
        if result:
            raise Exception(
                'create endpoints failed, errror={}'.format(result))


class Glance(DockerComponent):
    NAME = 'glance'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/glance': '/var/log/glance',
               '/var/lib/glance/images': '/var/lib/glance/images'}


class Cinder(DockerComponent):
    NAME = 'cinder'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/cinder': '/var/log/cinder'}


class NeutronServer(DockerComponent):
    NAME = 'neutron-server'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron'}


class NeutronDhcpAgent(DockerComponent):
    NAME = 'neutron-dhcp-agent'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron',
               '/var/run/openvswitch': '/var/run/openvswitch'}


class NeutronOVSAgent(DockerComponent):
    NAME = 'neutron-ovs-agent'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron',
               '/var/run/openvswitch': '/var/run/openvswitch'}


class NovaApi(DockerComponent):
    NAME = 'nova-api'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/nova': '/var/log/nova'}


class NovaScheduler(DockerComponent):
    NAME = 'nova-scheduler'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron'}


class NovaConductor(DockerComponent):
    NAME = 'nova-conductor'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron'}


class NovaCompute(DockerComponent):
    NAME = 'nova-compute'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/nova': '/var/log/nova',
               '/var/run/openvswitch': '/var/run/openvswitch'}


def list_all():
    return [
        Mariadb, Memcached, Rabbitmq,
        Keystone,
        Glance, Cinder,
        NeutronServer, NeutronDhcpAgent, NeutronOVSAgent,
        NovaApi, NovaConductor, NovaScheduler, NovaCompute
    ]


def get_component(name):
    global COMPONENT_DRIVERS
    if COMPONENT_DRIVERS is None:
        COMPONENT_DRIVERS = {c.NAME: c() for c in list_all()}
    if name not in COMPONENT_DRIVERS:
        raise Exception('component not found: {}'.format(name))
    return COMPONENT_DRIVERS[name]
