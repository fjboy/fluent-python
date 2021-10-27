from __future__ import print_function
from fp_lib.common import cliparser
from fp_lib.common import log
from fpstackutils.openstack import utils


LOG = log.getLogger(__name__)


class CleanUpServers(cliparser.CliBase):
    NAME = 'cleanup-servers'
    ARGUMENTS = [
        cliparser.Argument('-w', '--workers', type=int, default=10,
                           help='The workers to cleanup, default is 10'),
        cliparser.Argument('-n', '--name',
                           help='Instance name, e.g. test-vm')]

    def __call__(self, args):
        openstack_utils = utils.OpenstaskUtils()
        openstack_utils.cleanup_servers(name=args.name, workers=args.workers)


class InitResources(cliparser.CliBase):
    NAME = 'init-resources'
    ARGUMENTS = [
        cliparser.Argument('name_prefix', help='name prefix of resources'),
        cliparser.Argument('-n', '--net-num', default=1,
                           help='The num of network.')]

    def __call__(self, args):
        openstack_utils = utils.OpenstaskUtils()
        openstack_utils.init_resources(args.name_prefix, net_num=args.net_num)


class VMLifeCycle(cliparser.CliBase):
    NAME = 'vm-lifecycle'
    ARGUMENTS = [
        cliparser.Argument('image_id', help='image id'),
        cliparser.Argument('flavor_id', help='flavor id'),
        cliparser.Argument('-w', '--worker', type=int, default=1,
                           help='worker'),
        cliparser.Argument('-t', '--times', type=int, default=1,
                           help='run times')
    ]

    def __call__(self, args):
        openstack_utils = utils.OpenstaskUtils()
        openstack_utils.vm_lifecycle(args.image_id, args.flavor_id,
                                     worker=args.worker,
                                     times=args.times)
