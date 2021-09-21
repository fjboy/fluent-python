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

deploy_opts = [
    config.MapOption('components', default=DEFAULT_COMPONENTS),
    config.Option('build_target', default='zbw/centos7'),
    config.Option('build_yum_repo', default='centos7-163.repo'),
    
]
openstack_opts = [
    config.Option('memcached_servers', default='memcached-server1:11211'),
]


CONF = config.ConfigOpts()
CONF.register_opts(docker_opts, group='docker')
CONF.register_opts(deploy_opts, group='deploy')
CONF.register_opts(openstack_opts, group='openstack')
