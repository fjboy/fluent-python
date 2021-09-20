import sys

from fplib.common import cliparser
from fplib.common import log

if './' not in sys.path:
    sys.path.append('./')

from common import deployment

LOG = log.getLogger(__name__)

class DeployCmd(cliparser.CliBase):
    NAME = 'deploy'
    ARGUMENTS = [
        cliparser.Argument('component', help='component', choices=['mariadb']),
        cliparser.Argument('-v', '--verbose', action='store_true',
                           help='show details'),
    ]

    def __call__(self, args):
        manager = deployment.DeploymentBase()
        manager.deploy(args.component, verbose=args.verbose)


def main():
    cli_parser = cliparser.SubCliParser('Docker Openstack Deploy Utils')
    cli_parser.register_clis(DeployCmd)
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1

if __name__ == '__main__':

    sys.exit(main())
