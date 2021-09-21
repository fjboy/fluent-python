import sys
import socket

from fplib.common import cliparser
from fplib.common import log

if './' not in sys.path:
    sys.path.append('./')

from common import config
from common import deployment

CONF = config.CONF
LOG = log.getLogger(__name__)


COMPONENTS = [
    'mariadb', 'rabbitmq', 'memcached',
    'keystone', 'glance', 'cinder',
    'neutron-server', 'neutron-dhcp-agent', 'neutron-ovs-agent',
    'nova-api', 'nova-scheduler', 'nova-conductor', 'nova-compute'
]


class DeployCmd(cliparser.CliBase):
    NAME = 'deploy'
    ARGUMENTS = [
        cliparser.Argument('component', nargs='?', help='component', choices=COMPONENTS),
        cliparser.Argument('-v', '--verbose', action='store_true',
                           help='show details'),
    ]

    def __call__(self, args):
        from fplib.common import config
        manager = deployment.DeploymentBase(verbose=args.verbose)
        if args.component:
            manager.deploy(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if not socket.gethostname() in host_list:
                continue
            manager.deploy(component)


def main():
    cli_parser = cliparser.SubCliParser('Docker Openstack Deploy Utils')
    cli_parser.register_clis(DeployCmd)
    CONF.load('docker_stack.cfg')
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
