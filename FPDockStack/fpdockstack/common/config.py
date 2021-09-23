from fplib.common import config


docker_opts = [
    config.Option('build_file', default='Dockerfile'),
    config.Option('build_target', default='zbw/centos7'),
    config.Option('build_yum_repo', default='centos7-163.repo'),
]

DEFAULT_COMPONENTS = """
mariadb:localhost
memcached:localhost
rabbitmq:localhost
keystone:localhost
"""

DEFAULT_COMPONENT_HOST = """
mariadb:mariadb-server
memcached:memcached
rabbitmq:rabbitmq-server
keystone:keystone-server
neutron-sever:neutron-server
glance-sever:glance-server
cinder-server:cinder-server
nova-server:nova-server
"""
DEFAULT_MARIADB_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
/var/log/mariadb:/var/log/mariadb
"""
DEFAULT_KEYSTONE_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
"""
DEFAULT_NEUTRON_SERVER_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
-v /var/log/neutron:/var/log/neutron
"""
DEFAULT_NEUTRON_OVS_AGENT_VOLUMES = """
/etc/hosts:/etc/hosts
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
/sys/fs/cgroup:/sys/fs/cgroup
"""
DEFAULT_NEUTRON_DHCP_AGENT_VOLUMES = """
/etc/hosts:/etc/hosts
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
/sys/fs/cgroup:/sys/fs/cgroup
"""
DEFAULT_GLANCE_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
"""

DEFAULT_CINDER_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
"""

DEFAULT_CINDER_VOLUMES = """
/etc/hosts:/etc/hosts
/sys/fs/cgroup:/sys/fs/cgroup
/var/log/keystone:/var/log/keystone
/var/log/httpd:/var/log/httpd
"""

deploy_opts = [
    config.MapOption('components', default=DEFAULT_COMPONENTS),
    config.MapOption('component_host', default=DEFAULT_COMPONENT_HOST),
    config.Option('build_target', default='zbw/centos7'),
    config.Option('build_yum_repo', default='centos7-163.repo'),
    config.ListOption('mariadb_volumes', default=DEFAULT_MARIADB_VOLUMES),
    config.ListOption('keystone_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    config.ListOption('neutron_server_volumes', default=DEFAULT_NEUTRON_SERVER_VOLUMES),
    config.ListOption('neutron_dhcp_agent_volumes',
                      default=DEFAULT_NEUTRON_DHCP_AGENT_VOLUMES),
    config.ListOption('neutron_ovs_volumes',
                      default=DEFAULT_NEUTRON_OVS_AGENT_VOLUMES),
    config.ListOption('glance_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    config.ListOption('cinder_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    config.ListOption('nova_api_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    config.ListOption('nova_compute_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
]

openstack_opts = [
    config.Option('memcached_servers', default='memcached-server1:11211'),
]


CONF = config.ConfigOpts()
CONF.register_opts(docker_opts, group='docker')
CONF.register_opts(deploy_opts, group='deploy')
CONF.register_opts(openstack_opts, group='openstack')
