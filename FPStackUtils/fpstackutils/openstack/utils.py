from __future__ import print_function
from concurrent import futures
import eventlet
import threading
import contextlib

from fp_lib.common import log
from fpstackutils.openstack import client

LOG = log.getLogger(__name__)


class OpenstaskUtils(object):
    progress_format = '{}% {}'

    def __init__(self):
        super(OpenstaskUtils, self).__init__()
        self.openstack = client.OpenstackClient.create_instance()

    def get_deletable_servers(self, name=None):
        LOG.info('get servers')
        servers = []
        for s in self.openstack.nova.servers.list():
            if name and (name not in s.name):
                LOG.info('skip server: %s(%s)', s.name, s.id)
                continue
            if getattr(s, 'OS-EXT-STS:task_state') == 'deleting':
                continue
            servers.append(s)
        return servers

    def cleanup_servers(self, name=None, workers=None):
        workers = workers or 1
        servers = self.get_deletable_servers(name=name)
        self.percent = 0

        while len(servers) > 0:
            LOG.info('delete %s vms ...' % len(servers))
            with self.start_progress(len(servers)) as progress:
                deleted = 0
                with futures.ThreadPoolExecutor(
                        max_workers=workers) as executor:
                    for _ in executor.map(self._delete, servers):
                        deleted += 1
                        progress['completed'] = deleted

            servers = self.get_deletable_servers(name=name)

    def _delete(self, server):
        try:
            self.openstack.nova.servers.delete(server.id)
        except Exception as e:
            LOG.error(e)

    @contextlib.contextmanager
    def start_progress(self, total):
        self.percent = 0
        progress = {'completed': 0, 'total': total}
        t = threading.Thread(target=self.print_progress, args=(progress,))
        t.setDaemon(True)
        t.start()
        yield progress
        t.join()

    def print_progress(self, progress, interval=1):
        while True:
            percent = progress['completed'] * 100 / progress['total']
            if percent >= 100:
                break
            print(self.progress_format.format(percent, '#' * percent),
                  end='\r')
            eventlet.sleep(interval)
        print()

    def create_net(self, name_prefix, index=1):
        name = '{}-net{}'.format(name_prefix, index)
        LOG.info('create network %s', name)
        net = self.openstack.neutron.create_network({'name': name})
        LOG.info('create subnet')
        subnet = self.openstack.neutron.create_subnet({
            'cidr': "192.168.{}.0/24".format(index),
            'ip_version': 4,
            'network_id': net['id'],
            'name': '{}-subnet{}'.format(name_prefix, index)
        })
        return net, subnet

    def create_sg_with_rules(self, name_prefix, rules=None):
        name = '{}-sg'.format(name_prefix)
        LOG.info('create security group %s', name)
        sg = self.openstack.neutron.create_security_group({'name': name})
        if not rules:
            return
        for rule in rules:
            rule.update({'security_group_id': sg['id'],
                         'name': '{}-sg-rule'.format(name_prefix)})
            self.openstack.neutron.create_security_group_rule(
                rule.update()
            )

    def create_falvor(self, name_prefix, ram_gb, vcpus, disk):
        name = '{}-{}g{}v'.format(name_prefix, ram_gb, vcpus)
        LOG.info('create flavor %s', name)
        return self.openstack.nova.flavors.create(name, ram_gb * 1024,
                                                  vcpus, disk)

    def init_resources(self, name_prefix, net_num=1):
        for i in range(net_num):
            self.create_net(name_prefix, index=i + 1)
        LOG.info('create security group allow all')
        self.create_sg_with_rules(name_prefix, rules=[
            {"direction": "ingress", "ethertype": "IPv4", "protocol": "tcp"},
            {"direction": "egress", "ethertype": "IPv4", "protocol": "tcp"},
            {"direction": "ingress", "ethertype": "IPv4", "protocol": "icmp"},
            {"direction": "egress", "ethertype": "IPv4", "protocol": "icmp"},
        ])
        for config in [(1, 1, 10), (4, 4, 20), (8, 8, 40)]:
            self.create_falvor(name_prefix, config[0], config[1], config[2])

    def _get_nics(self, net_ids=None, port_ids=None):
        nics = []
        for net_id in net_ids or []:
            nics.append({'net-id': net_id})
        for port_id in port_ids or []:
            nics.append({'port-id': port_id})
        return nics

    def vm_lifecycle(self, image_id, flavor_id, net_ids=None, port_ids=None,
                     worker=1, times=1):
        nics = self._get_nics(net_ids=net_ids, port_ids=port_ids)
        LOG.debug('create with nics: %s', nics)

        def _run():
            vm = self.openstack.create_vm(image_id, flavor_id, nics=nics, 
                                          wait=True)
            self.openstack.delete_vm(vm.id)

        with futures.ThreadPoolExecutor(max_workers=worker) as executor:
            tasks = [executor.submit(_run) for i in range(times)]
            for task in tasks:
                task.done()
