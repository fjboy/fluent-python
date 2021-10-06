from ntpath import join
import docker
import json
import socket
import os
import re
import yaml
from docker import client
from docker import errors

from fp_lib.common import log
from common import config
from common.lib import openstackapi

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
        self._customs_config = None

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
        LOG.debug('run container with volumes: %s', self.VOLUMES)
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
        self.update_hosts(self.NAME)
        if not self.running():
            LOG.error('config failed, %s is not running', self.NAME)
            return
        LOG.info('[%s] register service', self.NAME)
        self.register_service()
        self.register_user()

        self.update_component_config()
        self.update_customs_config()

    def get_db_password(self, db):
        return CONF.openstack.db_identity.get(db, '')

    def get_auth_password(self, user):
        return CONF.openstack.auth_identity.get(user, '')

    def get_deploy_hosts(self, component):
        return CONF.deploy.components.get(component)

    def get_memcache_servers(self, join=None):
        hosts = self.get_deploy_hosts(Memcached.NAME)
        servers = ['{}:11211'.format(h) for h in hosts.split(',')]
        if join:
            return ','.join(servers)
        else:
            return servers

    def run_cmd_in_container(self, cmd, user=None, container=None):
        if not container:
            container = self.docker.containers.get(self.NAME)
        if user:
            run_cmd = ['su', '-s', '/bin/sh', '-c', ' '.join(cmd), user]
        else:
            run_cmd = cmd
        LOG.debug('RUN CMD: %s', run_cmd)
        output = container.exec_run(run_cmd)
        LOG.debug('RESULT : %s', output)
        return output

    def register_service(self):
        """register service
        """
        pass

    def register_user(self):
        """register user
        """
        pass

    def get_openstack_client(self):
        return openstackapi.OpenstackClient(
            'http://keystone-server:35357/v3',
            username='admin', project_name='admin',
            user_domain_name='Default', project_domain_name='Default',
            password=CONF.openstack.admin_password)

    def update_hosts(self, component):
        LOG.info('update hosts for %s', component)
        component_host = self.get_component_host(component)
        if not component_host:
            return
        component_ip = self.get_component_ip(component)
        with open('/etc/hosts', 'r') as f:
            lines = f.readlines()

        for line in lines:
            matched = re.match(
                r' *{} +{}'.format(component_ip, component_host), line)
            if matched:
                return
        else:
            with open('/etc/hosts', 'a+') as f:
                f.write('{} {}\n'.format(component_ip, component_host))

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

    def update_customs_config(self):
        container = self.docker.containers.get(self.NAME)
        LOG.info('[%s] update constoms config', self.NAME)
        constom_config = self.get_constom(self.NAME)
        for file, configs in constom_config.items():
            self._update_config(file, configs, container)

    def update_component_config(self):
        LOG.info('[%s] update component config', self.NAME)
        container = self.docker.containers.get(self.NAME)
        config_map = self.get_config_map()
        for file, configs in config_map.items():
            self._update_config(file, configs, container)

    def _update_config(self, file, configs, container):
        for section, options in configs.items():
            for option, value in options.items():
                cmd = ['openstack-config', '--set', file, 
                       section, option, value]
                result = self.run_cmd_in_container(cmd, container=container)
                if not result:
                    continue
                raise Exception('update {} failed, error={}'.format(file,
                                                                     result))

    def get_openstack_rabbitmq_url(self):
        return 'rabbit://{}:{}@rabbitmq-server'.format(
            CONF.openstack.rabbitmq_user, CONF.openstack.rabbitmq_password,
        )

    def get_keystone_authtoken_config(self, username):
        return {'auth_uri': 'http://keystone-server:5000',
                'auth_url': 'http://keystone-server:35357',
                'memcached_servers': CONF.openstack.memcached_servers,
                'username': username,
                'password': self.get_auth_password(username),
                'region_name': 'RegionOne',
                'auth_type': 'password',
                'project_name': 'service',
                'project_domain_name': 'Default',
                'user_domain_name': 'Default',
            }

    def get_constom(self, component):
        if not self._customs_config:
            with open(CONF.openstack.customs_config) as f:
                self._customs_config = yaml.load(f.read(),
                                                 Loader=yaml.FullLoader)
        LOG.debug('%s constom config: %s',
                  component, self._customs_config.get(component))
        return self._customs_config.get(component) or {}

    def get_config_map(self):
        return {}

    def get_localhostname(self):
        return socket.gethostname()


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

    def update_component_config(self):
        for component, _ in CONF.deploy.components.items():
            if component == 'keystone':
                self.init_database('keystone', 'keystone')
            elif component == 'neutron-server':
                self.init_database('neutron', 'neutron')
            elif component == 'nova-api':
                self.init_database('nova', 'nova')
                self.init_database('nova_api', 'nova')
                self.init_database('nova_cell0', 'nova')
            if component == 'glance-api':
                self.init_database('glance', 'glance')
            if component == 'cinder-api':
                self.init_database('cinder', 'cinder')

    def init_database(self, database, user):
        LOG.info('[%s] init database %s', self.NAME, database)
        container = self.docker.containers.get(self.NAME)
        result = self.run_sql_in_container(self.SQL_CREATE_DB.format(database),
                                           container=container)
        if result:
            raise Exception('create database failed {}'.format(result))
        password = self.get_db_password(user)

        LOG.info('[%s] grant for %s', self.NAME, database)
        self.run_sql_in_container(
            self.SQL_GRANT_LOCALHOST.format(database, user, password),
            container=container)
        self.run_sql_in_container(
            self.SQL_GRANT_ALL.format(database, user, password),
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
        return ['-p', str(CONF.memcached.port),
                '-u', CONF.memcached.user,
                '-m', str(CONF.memcached.maxcache),
                '-c', str(CONF.memcached.maxconn),
                '-l', address]


class Rabbitmq(DockerComponent):
    NAME = 'rabbitmq'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/var/log/mariadb': '/var/log/mariadb'}

    def update_component_config(self):
        container = self.docker.containers.get(self.NAME)
        ip = CONF.rabbitmq.rabbitmq_node_ip
        if not ip:
            addr = socket.getaddrinfo(socket.gethostname(), 'http')
            ip = addr[0][4][0]
        container.exec_run(['echo', 'RABBITMQ_NODE_IP_ADDRESS={}'.format(ip),
                            '>>', '/etc/rabbitmq/rabbitmq-env.conf'])

    def update_customs_config(self):
        container = self.docker.containers.get(self.NAME)
        self._run_rabbimqctl(['add_user', CONF.openstack.rabbitmq_user,
                             CONF.openstack.rabbitmq_password],
                             container)
        self._run_rabbimqctl(['set_permissions', '-p', '/',
                              CONF.openstack.rabbitmq_user, '.*', '.*', '.*'],
                             container)
        self._run_rabbimqctl(
            ['set_user_tags', CONF.openstack.rabbitmq_user, 'administrator'],
            container)

    def _run_rabbimqctl(self, cmd, container):
        run_cmd = ['rabbitmqctl'] + cmd
        self.run_cmd_in_container(run_cmd, container=container)


class Keystone(DockerComponent):
    NAME = 'keystone'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/keystone': '/var/log/keystone',
               '/var/log/httpd': '/var/log/httpd'}
    CONNECTION = 'mysql+pymysql://keystone:{}@{}/keystone'

    def get_config_map(self):
        pwd = self.get_db_password(self.NAME)
        return {
            '/etc/keystone/keystone.conf': {
                'database': {
                    'connection': self.CONNECTION.format(pwd, 'mariadb-server')
                }
            }
        }

    def config(self):
        super(Keystone, self).config()

        self.make_admin_openrc()
        os.chmod('/var/log/keystone', 777)

        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container(['keystone-manage', 'db_sync'],
                                           user='keystone')
        if result:
            raise Exception('db sync failed, error={}'.format(result))

        LOG.info('[%s] create endpoints', self.NAME)
        cmd = ['keystone-manage', 'bootstrap', '--bootstrap-password',
               CONF.openstack.admin_password,
               '--bootstrap-admin-url', 'http://keystone-server:35357/v3/',
               '--bootstrap-internal-url', 'http://keystone-server:35357/v3/',
               '--bootstrap-public-url', 'http://kestone-server:5000/v3/',
               '--bootstrap-region-id', 'RegionOne']
        result = self.run_cmd_in_container(cmd)
        if result:
            raise Exception('run bootstrap failed, error={}'.format(result))

    def make_admin_openrc(self):
        LOG.info('[%s] make admin openrc', self.NAME)
        openrc_lines = [
            'export OS_USERNAME=admin\n',
            'export OS_PASSWORD={}\n'.format(CONF.openstack.admin_password),
            'export OS_PROJECT_NAME=admin\n',
            'export OS_USER_DOMAIN_NAME=Default\n',
            'export OS_PROJECT_DOMAIN_NAME=Default\n',
            'export OS_AUTH_URL=http://keystone-server:35357/v3\n',
            'export OS_IDENTITY_API_VERSION=3\n',
            'export OS_IMAGE_API_VERSION=2\n',
            'export OS_VOLUME_API_VERSION=2\n',
            'export OS_REGION_NAME=RegionOne\n',
        ]
        file_path = os.path.join(os.path.expanduser('~'), 'admin_openrc.sh') 
        with open(file_path, 'w') as f:
            f.writelines(openrc_lines)


class GlanceApi(DockerComponent):
    NAME = 'glance-api'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/glance': '/var/log/glance',
               '/var/lib/glance/images': '/var/lib/glance/images'}
    CONNECTION = 'mysql+pymysql://glance:{}@{}/glance'

    def register_user(self):
        LOG.info('[%s] create user', self.NAME)
        cli = self.get_openstack_client()
        cli.create_user('glance', self.get_auth_password('glance'),
                        'service', role='admin')

    def register_service(self):
        LOG.info('[%s] create endpoints', self.NAME)
        cli = self.get_openstack_client()
        cli.create_service_endpoints('glance', 'image', 'RegionOne',
                                     'http://glance-server:9292',
                                     'http://glance-server:9292',
                                     'http://glance-server:9292',
                                     description='OpenStack Image service')

    def config(self):
        self.run_cmd_in_container(['yum', 'install', '-y', 'openstack-utils'])

        super(GlanceApi, self).config()

        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container(['glance-manage', 'db_sync'],
                                           user='glance',
                                           )
        if result and (b'synced successfully' not in result and
                       b'Database is up to date' not in result):
            raise Exception('db sync failed, error={}'.format(result))

    def get_config_map(self):
        pwd = self.get_db_password('glance')
        if not pwd:
            raise Exception('glance db password not set')
        # docker exec -it glance openstack-config --set ${GLANCE_CONF_API} DEFAULT bind_host ${GLANCE_HOST}
        # docker exec -it glance openstack-config --set ${GLANCE_CONF_API} DEFAULT registry_host ${GLANCE_HOST}
        return {
            '/etc/glance/glance-api.conf': {
                'keystone_authtoken':
                    self.get_keystone_authtoken_config('glance'),
                'cinder': {
                    'os_region_name': 'RegionOne'
                },
                'database': {
                    'connection': self.CONNECTION.format(pwd, Mariadb.NAME)
                },
            }
        }


class GlanceRegistry(GlanceApi):
    NAME = 'glance-registry'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/glance': '/var/log/glance',
               '/var/lib/glance/images': '/var/lib/glance/images'}

    def config(self):
        self.run_cmd_in_container(['yum', 'install', '-y', 'openstack-utils'])
        super(CinderApi, self).config()
        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container(['glance-manage', 'db_sync'],
                                           user='glance',
                                           )
        if result:
            raise Exception('db sync failed, error={}'.format(result))

    def get_config_map(self):
        pwd = self.get_db_password(self.NAME)
        return {
            '/etc/glance/glance-registry.conf': {
                'keystone_authtoken': 
                    self.get_keystone_authtoken_config('glance'),
                'database': {
                    'connection': self.CONNECTION.format(pwd, Mariadb.NAME)
                },

            }
        }


class CinderApi(DockerComponent):
    NAME = 'cinder-api'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/cinder': '/var/log/cinder'}

    def register_user(self):
        cli = self.get_openstack_client()
        LOG.info('[%s] create user', self.NAME)
        cli.create_user('cinder', self.get_auth_password('cinder'),
                        'service', role='admin')
        
    def register_service(self):
        LOG.info('[%s] create endpoints', self.NAME)
        cli = self.get_openstack_client()
        cli.create_service_endpoints(
            'cinderv2', 'volumev2', 'RegionOne',
            'http://cinder-server:8776/v2/%(project_id)s',
            'http://cinder-server:8776/v2/%(project_id)s',
            'http://cinder-server:8776/v2/%(project_id)s',
            description='OpenStack Block Storage')

        cli.create_service_endpoints(
            'cinderv3', 'volumev3', 'RegionOne',
            'http://cinder-server:8776/v3/%(project_id)s',
            'http://cinder-server:8776/v3/%(project_id)s',
            'http://cinder-server:8776/v3/%(project_id)s',
            description='OpenStack Block Storage')

    def get_config_map(self):
        return {}

class NeutronServer(DockerComponent):
    NAME = 'neutron-server'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/sys/fs/cgroup': '/sys/fs/cgroup',
               '/var/log/neutron': '/var/log/neutron'}
    CONNECTION = 'mysql+pymysql://neutron:{}@{}/neutron'

    def register_user(self):
        cli = self.get_openstack_client()
        LOG.info('[%s] create user', self.NAME)
        cli.create_user('neutron', self.get_auth_password('neutron'),
                        'service', role='admin')

    def register_service(self):
        LOG.info('[%s] create endpoints', self.NAME)
        cli = self.get_openstack_client()
        cli.create_service_endpoints(
            'neutron', 'network', 'RegionOne',
            'http://neutron-server:9696',
            'http://neutron-server:9696',
            'http://neutron-server:9696',
            description='OpenStack Networking')

    def config(self):
        self.run_cmd_in_container(['yum', 'install', '-y', 'openstack-utils'])
        super(NeutronServer, self).config()

        self.run_cmd_in_container([
            'ln', '-s', '/etc/neutron/plugins/ml2/ml2_conf.ini',
            '/etc/neutron/plugin.ini'])

        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container([
            'neutron-db-manage',
            '--config-file', '/etc/neutron/neutron.conf',
            '--config-file', '/etc/neutron/plugins/ml2/ml2_conf.ini',
            'upgrade', 'head',],
            user='neutron')
        if result and b'OK' not in result:
            raise Exception('db sync failed, error={}'.format(result))

    def get_config_map(self):
        pwd = self.get_db_password('neutron')
        return {
            '/etc/neutron/neutron.conf': {
                'DEFAULT': {
                    'transport_url': self.get_openstack_rabbitmq_url(),
                },
                'keystone_authtoken': 
                    self.get_keystone_authtoken_config('neutron'),
                'database': {
                    'connection': self.CONNECTION.format(pwd, 'mariadb-server')
                },
                'nova': {
                    'auth_url': 'http://keytone-server:35357',
                    'region_name': 'RegionOne',
                    'project_name': 'service',
                    'username': 'nova',
                    'password': self.get_auth_password('nova'),
                },
            },
        }


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
    CONNECTION = 'mysql+pymysql://nova:{}@{}/nova'
    API_CONNECTION = 'mysql+pymysql://nova:{}@{}/nova_api'

    def register_user(self):
        LOG.info('[%s] create user', self.NAME)
        cli = self.get_openstack_client()
        cli.create_user('nova', self.get_auth_password('nova'),
                        'service', role='admin')

    def register_service(self):
        LOG.info('[%s] create endpoints', self.NAME)
        cli = self.get_openstack_client()
        cli.create_service_endpoints('nova', 'compute', 'RegionOne',
                                     'http://nova-server:8774/v2.1',
                                     'http://nova-server:8774/v2.1',
                                     'http://nova-server:8774/v2.1',
                                     description='OpenStack Compute')

    def config(self):
        self.run_cmd_in_container(['yum', 'install', '-y', 'openstack-utils'])
        super(NovaApi, self).config()

        LOG.info('[%s] db sync', self.NAME)
        result = self.run_cmd_in_container(
            ['nova-manage', 'api_db', 'sync'], user='nova')
        if result:
            raise Exception('api_db sync failed, error={}'.format(result))

        result = self.run_cmd_in_container(
            ['nova-manage', 'cell_v2', 'map_cell0'], user='nova')
        if result and b'already setup' not in result:
            raise Exception('map_cell0 failed, error={}'.format(result))

        result = self.run_cmd_in_container(
            ['nova-manage', 'cell_v2', 'create_cell', '--name=cell1'],
            user='nova')
        if result and (b'error' in result or b'ERROR' in result):
            raise Exception(
                'create_cell cell1 failed, error={}'.format(result))

        result = self.run_cmd_in_container(
            ['nova-manage', 'db', 'sync'], user='nova')
        if result and b'Error' in result:
            raise Exception('db sync failed, error={}'.format(result))

    def get_config_map(self):
        pwd = self.get_db_password('nova')
        if not pwd:
            raise Exception('nova db password not set')
        return {
            '/etc/nova/nova.conf': {
                 'DEFAULT': {
                    'transport_url': self.get_openstack_rabbitmq_url(),
                    'osapi_compute_listen':
                        self.get_localhostname(),
                    'my_ip': self.get_component_ip(self.NAME),
                },
                'keystone_authtoken':
                    self.get_keystone_authtoken_config('nova'),
                'cinder': {
                    'os_region_name': 'RegionOne'
                },
                'database': {
                    'connection': self.CONNECTION.format(
                        self.get_db_password('nova'), 'mariadb-server')
                },
                'api_database': {
                      'connection':
                          self.API_CONNECTION.format(
                              self.get_db_password('nova'),
                              'mariadb-server')
                },
                'cache': {
                    'memcache_servers': self.get_memcache_servers(join=',')
                },
                'glance':{
                    'api_servers': 'http://glance-server:9292'
                }
            }
        }


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
        GlanceApi, GlanceRegistry,
        CinderApi,
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
