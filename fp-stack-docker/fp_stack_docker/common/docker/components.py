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
        pass


class Mariadb(DockerComponent):
    NAME = 'mariadb'
    VOLUMES = {'/etc/hosts': '/etc/hosts',
               '/var/log/mariadb': '/var/log/mariadb'}


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

    def config(self):
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


def list_components():
    return [
        Mariadb, Memcached, Rabbitmq,
        Keystone,
        Glance, Cinder,
        NeutronServer, NeutronDhcpAgent, NeutronOVSAgent,
        NovaApi, NovaConductor, NovaScheduler, NovaCompute
    ]
