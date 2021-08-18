import sys

from fplib.common import cliparser
from fplib.common import log
from fputils.base import fs
from fputils.base import setpip
from fputils.base import code
from fputils.base import confeditor

LOG = log.getLogger(__name__)


def main():
    cli_parser = cliparser.SubCliParser('Fluent Python Utils Base')
    cli_parser.register_clis(fs.PyTac, setpip.SetPip,
                             code.JsonGet, code.Md5Sum,
                             confeditor.ConfigList,
                             code.GeneratePassword)
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
