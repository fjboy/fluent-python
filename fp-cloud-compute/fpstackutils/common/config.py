from fp_lib.common import cfg

from fpstackutils.common import constants

CONF = cfg.CONF

default_opts = [
    cfg.BooleanOption('debug', default=False),
]

openstack_opts = [
    cfg.Option('image_id'),
    cfg.Option('flavor_id'),
    cfg.ListOption('net_ids'),
    cfg.Option('attach_net'),
    cfg.BooleanOption('boot_from_volume', default=False),
    cfg.IntOption('volume_size', default=10),
    cfg.Option('boot_az'),
]

task_opts = [
    cfg.IntOption('total', default=1),
    cfg.IntOption('worker', default=1),
    cfg.BooleanOption('attach_net', default=False),
    cfg.ListOption('vm_test_actions', default=constants.ACTIONS_ALL),

    cfg.IntOption('attach_net_nums', default=1),
    cfg.IntOption('attach_net_times', default=1),

    cfg.IntOption('attach_volume_nums', default=1),
    cfg.IntOption('attach_volume_times', default=1),

    cfg.IntOption('attach_port_nums', default=1),
    cfg.IntOption('attach_port_tims', default=1),

    cfg.IntOption('boot_wait_interval', default=1),
    cfg.IntOption('boot_wait_timeout', default=600),

    cfg.IntOption('detach_interface_wait_interval', default=1),
    cfg.IntOption('detach_interface_wait_timeout', default=60),

    cfg.IntOption('migrate_wait_interval', default=5),
    cfg.IntOption('migrate_wait_timeout', default=60),
    cfg.IntOption('evacuate_vms_num', default=1),
    cfg.BooleanOption('cleanup_error', default=True),
]


CONF.register_opts(default_opts)
CONF.register_opts(openstack_opts, group='openstack')
CONF.register_opts(task_opts, group='task')
