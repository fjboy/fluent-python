from fp_lib.common import cfg


CONF = cfg.CONF


DEFAULT_COMPONENTS = """
mariadb:localhost
memcached:localhost
rabbitmq:localhost
keystone:localhost
glance-api:localhost
"""

DEFAULT_DB_IDENTITY = """
keystone:keystone123
neutron:neutron123
nova:nova123
nova_api:nova123
cinder:cinder123
glance:glance123
"""
DEFAULT_AUTH_IDENTITY = """
keystone:keystone123
neutron:neutron123
nova:nova123
nova-api:nova123
cinder:cinder123
glance:glance123

"""

DEFAULT_ADMIN_PASSWORD = 'admin123'


default_opts = [
    cfg.Option('verbose', default=False),
]

deploy_opts = [
    cfg.MapOption('components', default=DEFAULT_COMPONENTS),
    cfg.MapOption('vip_mapping'),
]

docker_opts = [
    cfg.Option('build_file', default='Dockerfile'),
    cfg.Option('build_target', default='zbw/centos7'),
    cfg.Option('build_yum_repo', default='centos7-163.repo'),
]

openstack_opts = [
    cfg.Option('memcached_servers', default='memcached-server1:11211'),
    cfg.Option('transport_url', default='rabbit://openstack:openstack123@rabbitmq-server'),
    cfg.MapOption('db_identity', default=DEFAULT_DB_IDENTITY),
    cfg.MapOption('auth_identity', default=DEFAULT_AUTH_IDENTITY),
    cfg.Option('admin_password', default=DEFAULT_ADMIN_PASSWORD),
    cfg.Option('rabbitmq_user', default='openstack'),
    cfg.Option('rabbitmq_password', default='openstack123'),
    cfg.Option('customs_config'),
]

rabbitmq_opts = [
    cfg.Option('rabbitmq_node_ip', default=None),
]


PORT="11211"
USER="memcached"
MAXCONN="20000"
CACHESIZE="20480"


memcached_opts = [
    cfg.IntOption('port', default=11211),
    cfg.Option('user', default='memcached'),
    cfg.IntOption('maxconn', default=20000),
    cfg.IntOption('maxcache', default=20480),
    cfg.IntOption('address', ),
]


CONF.register_opts(default_opts)
CONF.register_opts(deploy_opts, group='deploy')
CONF.register_opts(docker_opts, group='docker')
CONF.register_opts(openstack_opts, group='openstack')
CONF.register_opts(memcached_opts, group='memcached')
CONF.register_opts(rabbitmq_opts, group='rabbitmq')

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

