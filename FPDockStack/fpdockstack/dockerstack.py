import sys
import socket

from fplib.common import cliparser
from fplib.common import log

if './' not in sys.path:
    sys.path.append('./')

from fpdockstack.common import config
from fpdockstack.common import deployment

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
        manager = deployment.DeploymentBase(verbose=args.verbose)
        if args.component:
            manager.deploy(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if (not socket.gethostname() in host_list) and \
               (not 'localhost' in host_list):
                continue
            manager.deploy(component)


class StartCmd(cliparser.CliBase):
    NAME = 'start'
    ARGUMENTS = [
        cliparser.Argument('component', nargs='?', help='component', choices=COMPONENTS),
        cliparser.Argument('-v', '--verbose', action='store_true',
                           help='show details'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase(verbose=args.verbose)
        if args.component:
            manager.start(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if (not socket.gethostname() in host_list) and \
               (not 'localhost' in host_list):
                continue
            manager.start(component)




class StopCmd(cliparser.CliBase):
    NAME = 'stop'
    ARGUMENTS = [
        cliparser.Argument('component', nargs='?', help='component', choices=COMPONENTS),
        cliparser.Argument('-v', '--verbose', action='store_true',
                           help='show details'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase(verbose=args.verbose)
        if args.component:
            manager.stop(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if (not socket.gethostname() in host_list) and \
               (not 'localhost' in host_list):
                continue
            manager.stop(component)


class CleanUPCmd(cliparser.CliBase):
    NAME = 'cleanup'
    ARGUMENTS = [
        cliparser.Argument('component', nargs='?', help='component', choices=COMPONENTS),
        cliparser.Argument('-v', '--verbose', action='store_true',
                           help='show details'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase(verbose=args.verbose)
        if args.component:
            manager.cleanup(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if (not socket.gethostname() in host_list) and \
               (not 'localhost' in host_list):
                continue
            manager.cleanup(component)


def main():
    cli_parser = cliparser.SubCliParser('Docker Openstack Deploy Utils')
    cli_parser.register_clis(DeployCmd, StartCmd, StopCmd, CleanUPCmd)
    CONF.load('docker_stack.cfg')
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
