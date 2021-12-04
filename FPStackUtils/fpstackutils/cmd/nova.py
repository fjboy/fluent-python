import sys

from fp_lib.common import cliparser
from fp_lib.common import log
from fpstackutils.commands import nova

LOG = log.getLogger(__name__)


def main():
    cli_parser = cliparser.SubCliParser('Python Nova Utils')
    cli_parser.register_clis(nova.VMCleanup,
                             nova.ResourcesInit,
                             nova.VMTest)
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
