import sys

from fplib.common import cliparser
from fplib.common import log
from fpstackutils.commands import nova

LOG = log.getLogger(__name__)


def main():
    cli_parser = cliparser.SubCliParser('Fluent Python Openstack Utils')
    cli_parser.register_clis(nova.CleanUpServers)
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
