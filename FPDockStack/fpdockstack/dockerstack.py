import os
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


class InstallCmd(cliparser.CliBase):
    NAME = 'install'
    ARGUMENTS = [
        cliparser.Argument('component', nargs='?', help='component',
                           choices=COMPONENTS),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
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
        cliparser.Argument('component', nargs='?', help='component',
                           choices=COMPONENTS),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
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
        cliparser.Argument('component', nargs='?', help='component',
                           choices=COMPONENTS),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
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
        cliparser.Argument('component', nargs='?', help='component',
                           choices=COMPONENTS),
        cliparser.Argument('-f', '--foce', action='store_true',
                           help='force to cleanup'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
        if args.component:
            manager.cleanup(args.component)
            return
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if (not socket.gethostname() in host_list) and \
               (not 'localhost' in host_list):
                continue
            manager.cleanup(component, force=args.force)


class StatusCmd(cliparser.CliBase):
    NAME = 'status'
    ARGUMENTS = [
        cliparser.Argument('-a', '--all', action='store_true',
                           help='show all components'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
        line_format = '{:20} {:10} {:10s}'
        print(line_format.format('Component', 'installed', 'status'))
        print(line_format.format('---------', '---------', '------'))
        for component, hosts in CONF.deploy.components.items():
            host_list = hosts.split(',')
            if args.all or (socket.gethostname() in host_list) or \
               ('localhost' in host_list):
                installed, status = manager.status(component)
                print(line_format.format(component,
                                         installed and 'yes' or 'no',
                                         status or 'not started'))


def main():
    cli_parser = cliparser.SubCliParser('Docker Openstack Deploy Utils')
    cli_parser.register_clis(InstallCmd, StartCmd, StopCmd, CleanUPCmd,
                             StatusCmd)
    
    
    CONF.load(os.path.join(os.path.dirname(__file__), 'docker_stack.cfg'))
    cli_args = cli_parser.parse_args()
    if hasattr(cli_args, 'verbose') and cli_args.verbose:
        CONF.set_cli('verbose', cli_parser._args.verbose)

    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
