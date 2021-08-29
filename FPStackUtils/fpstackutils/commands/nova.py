from __future__ import print_function
from fplib.common import cliparser
from fplib.common import log
from fpstackutils.openstack import nova as nova_lib


LOG = log.getLogger(__name__)


class CleanUpServers(cliparser.CliBase):
    NAME = 'cleanup-servers'
    ARGUMENTS = [
        cliparser.Argument('-w', '--workers', type=int, default=10,
                           help='The workers to cleanup, default is 10'),
        cliparser.Argument('-n', '--name',
                           help='Instance name, e.g. test-vm')]

    def __call__(self, args):
        nova_lib.concurrent_delete_servers(workers=args.workers,
                                           name=args.name)