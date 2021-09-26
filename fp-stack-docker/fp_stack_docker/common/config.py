from fp_lib.common import config


CONF = config.CONF


DEFAULT_COMPONENTS = """
mariadb:localhost
memcached:localhost
rabbitmq:localhost
keystone:localhost
"""

default_opts = [
    config.Option('verbose', default=False),
]

deploy_opts = [
    config.MapOption('components', default=DEFAULT_COMPONENTS),
    # config.MapOption('component_host', default=DEFAULT_COMPONENT_HOST),
    # config.ListOption('mariadb_volumes', default=DEFAULT_MARIADB_VOLUMES),
    # config.ListOption('keystone_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    # config.ListOption('neutron_server_volumes', default=DEFAULT_NEUTRON_SERVER_VOLUMES),
    # config.ListOption('neutron_dhcp_agent_volumes',
    #                   default=DEFAULT_NEUTRON_DHCP_AGENT_VOLUMES),
    # config.ListOption('neutron_ovs_volumes',
    #                   default=DEFAULT_NEUTRON_OVS_AGENT_VOLUMES),
    # config.ListOption('glance_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    # config.ListOption('cinder_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    # config.ListOption('nova_api_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
    # config.ListOption('nova_compute_volumes', default=DEFAULT_KEYSTONE_VOLUMES),
]

docker_opts = [
    config.Option('build_file', default='Dockerfile'),
    config.Option('build_target', default='zbw/centos7'),
    config.Option('build_yum_repo', default='centos7-163.repo'),
]

openstack_opts = [
    config.Option('memcached_servers', default='memcached-server1:11211'),
]

PORT="11211"
USER="memcached"
MAXCONN="20000"
CACHESIZE="20480"


memcached_opts = [
    config.IntOption('port', default=11211),
    config.Option('user', default='memcached'),
    config.IntOption('maxconn', default=20000),
    config.IntOption('maxcache', default=20480),
    config.IntOption('address'),
]


CONF.register_opts(default_opts)
CONF.register_opts(deploy_opts, group='deploy')
CONF.register_opts(docker_opts, group='docker')
CONF.register_opts(openstack_opts, group='openstack')
CONF.register_opts(openstack_opts, group='memcached')

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

