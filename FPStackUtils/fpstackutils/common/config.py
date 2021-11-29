from fp_lib.common import cfg

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
]

task_opts = [
    cfg.IntOption('total', default=1),
    cfg.IntOption('worker', default=1),

    cfg.BooleanOption('attach_net', default=False),
    cfg.IntOption('attach_net_nums', default=1),
    cfg.IntOption('attach_net_times', default=1),

    cfg.BooleanOption('attach_volume', default=False),
    cfg.IntOption('attach_volume_nums', default=1),
    cfg.IntOption('attach_volume_times', default=1),

    cfg.BooleanOption('attach_port', default=False),
    cfg.IntOption('attach_port_nums', default=1),
    cfg.IntOption('attach_port_tims', default=1),

    cfg.IntOption('detach_interface_check_interval', default=1),
    cfg.IntOption('detach_interface_timeout', default=60),
    cfg.BooleanOption('reboot', default=False),
]


CONF.register_opts(default_opts)
CONF.register_opts(openstack_opts, group='openstack')
CONF.register_opts(task_opts, group='task')
