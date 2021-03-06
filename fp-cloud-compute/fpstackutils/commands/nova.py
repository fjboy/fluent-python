import logging
import os

from fp_lib.common import cliparser
from fp_lib.common import log
from fpstackutils.openstack import manager

from fpstackutils.common import config

CONF = config.CONF
LOG = log.getLogger(__name__)


class VMCleanup(cliparser.CliBase):
    NAME = 'vm-cleanup'
    ARGUMENTS = [
        cliparser.Argument('-w', '--workers', type=int, default=10,
                           help='The workers to cleanup, default is 10'),
        cliparser.Argument('-n', '--name', help='VM name, e.g. test-vm'),
        cliparser.Argument('-s', '--status', help='VM status, e.g. error')]

    def __call__(self, args):
        vm_manager = manager.VMManager()
        vm_manager.cleanup_vms(name=args.name, workers=args.workers,
                               status=args.status)


class ResourcesInit(cliparser.CliBase):
    NAME = 'resources-init'
    ARGUMENTS = [
        cliparser.Argument('name_prefix', help='name prefix of resources'),
        cliparser.Argument('-n', '--net-num', default=1,
                           help='The num of network.')]

    def __call__(self, args):
        vm_manager = manager.VMManager()
        vm_manager.init_resources(args.name_prefix,
                                  net_num=args.net_num)


class VMTest(cliparser.CliBase):
    NAME = 'vm-test'
    ARGUMENTS = [
        cliparser.Argument('-c', '--conf', default='ec-nova.conf',
                           help='config file'),
    ]

    def __call__(self, args):
        if args.conf and not os.path.isfile(args.conf):
            LOG.error('config file %s is not exists', args.conf)
            return
        CONF.load(args.conf)
        if CONF.debug:
            log.set_default(level=logging.DEBUG)
        if args.debug:
            CONF.set_cli('debug', args.debug)
        LOG.debug('load config from %s', args.conf)
        vm_manager = manager.VMManager()
        vm_manager.test_vm()


class VMEvacuateTest(cliparser.CliBase):
    NAME = 'vm-evacuate-test'
    ARGUMENTS = [
        cliparser.Argument('-c', '--conf', default='ec-nova.conf',
                           help='config file'),
    ]

    def __call__(self, args):
        if args.conf and not os.path.isfile(args.conf):
            LOG.error('config file %s is not exists', args.conf)
            return
        CONF.load(args.conf)
        if CONF.debug:
            log.set_default(level=logging.DEBUG)
        if args.debug:
            CONF.set_cli('debug', args.debug)
        LOG.debug('load config from %s', args.conf)
        vm_manager = manager.VMManager()
        vm_manager.test_evacuate()
