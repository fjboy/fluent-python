import sys

from stevedore import extension

from fplib.common import cliparser
from fplib.common import log

LOG = log.getLogger(__name__)


def main():
    cli_parser = cliparser.SubCliParser('Fluent Python Utils Extensions')

    ext_manager = extension.ExtensionManager(
        namespace='fputils.extensions',
        invoke_on_load=True,
    )
    for name, ext in ext_manager.items():
        sub_commands = ext.obj
        LOG.debug('register sub commands for extension %s', name)
        cli_parser.register_clis(*sub_commands)
    try:
        cli_parser.call()
        return 0
    except KeyboardInterrupt:
        LOG.error("user interrupt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
