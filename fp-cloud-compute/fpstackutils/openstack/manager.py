from concurrent import futures
from datetime import datetime
import time

from novaclient import exceptions as nova_exc
from fp_lib.common import log
from fp_lib.common import waiter
from fp_lib.common import colorstr
from fp_lib.common import progressbar
from fp_lib.common import table

from fpstackutils.common import constants
from fpstackutils.common import config
from fpstackutils.common import exceptions
from fpstackutils.openstack import client

CONF = config.CONF
LOG = log.getLogger(__name__)


def check_if_skip(action):

    def wrapper(func):
        def wrapper_func(*args, **kwargs):
            if action not in CONF.task.vm_test_actions:
                LOG.warning('skip %s', action)
                return
            return func(*args, **kwargs)

        return wrapper_func

    return wrapper


class CleanUpManager(object):

    def __init__(self):
        self.cleanup_list = []

    def add(self, func, *args, **kwargs):
        self.cleanup_list.append((func, args or (), kwargs or {}))


    def cleanup(self):
        for func, args, kwargs in self.cleanup_list:
            try:
                func(*args, **kwargs)
            except Exception as e:
                LOG.warning('run %s failed, error=%s', func, e)
        self.cleanup_list = []


class VMManagerBase(object):

    def __init__(self):
        self.openstack = client.OpenstackClient.create_instance()
        self.flavors_cached = {}
        self.cleanup_manager = CleanUpManager()
        self._attach_net = CONF.openstack.attach_net

    @staticmethod
    def generate_name(resource):
        return 'test-{}-{}'.format(resource,
                                   datetime.now().strftime('%m%d-%H:%M:%S'))

    @staticmethod
    def _get_nics():
        if not CONF.openstack.net_ids:
            return 'none'
        return [{'net-id': net_id} for net_id in CONF.openstack.net_ids]

    def _get_flavor(self, flavor_id):
        if flavor_id not in self.flavors_cached:
            self.flavors_cached[flavor_id] = self.openstack.nova.flavors.get(
                CONF.openstack.flavor_id)
        return self.flavors_cached[flavor_id]

    def create_flavor(self, ram, vcpus, disk=0, metadata=None):
        flavor = self.openstack.nova.flavors.create(self.generate_name('flavor'),
                                                    ram, vcpus, disk)
        if metadata:
            flavor.set_keys(metadata)
        self.cleanup_manager.add(self.openstack.nova.flavors.delete, flavor.id)
        return flavor

    def get_available_services(self, host=None, binary=None):
        services = []
        for service in self.openstack.nova.services.list(host=host,
                                                         binary=binary):
            if service.status == 'enabled' and service.state == 'up':
                services.append(service)
        return services

    @staticmethod
    def get_vm_state(vm, refresh=False):
        if refresh:
            vm.get()
        return getattr(vm, 'OS-EXT-STS:vm_state')

    def get_task_state(self, vm, refresh=False):
        if refresh:
            vm = self.openstack.nova.servers.get(vm.id)
        return getattr(vm, 'OS-EXT-STS:task_state')

    def get_deletable_servers(self, name=None, status=None):
        LOG.debug('get servers, name=%s, status=%s', name, status)
        vms = []
        for vm in self.openstack.nova.servers.list():
            vm_state = self.get_vm_state(vm)
            LOG.debug('[vm: %s] name=%s, vm_state=%s',
                      vm.id, vm.name, vm_state)
            if name and (name not in vm.name):
                continue
            if status and vm_state != status:
                continue
            vms.append(vm)
        return vms

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

    def _wait_for_vm(self, vm, status=None, task_states=None,
                     ignore_vm_error=False, timeout=None, interval=1):
        if task_states is None:
            task_states = [None]
        if status is None:
            status = {'active'}
        if status:
            check_status = {status} if isinstance(status, str) else status
        else:
            check_status = []
        stop_time = time.time() + timeout if timeout else None
        while True:
            vm_state = self.get_vm_state(vm, refresh=True)
            task_state = self.get_task_state(vm)
            if vm_state == 'error':
                if not ignore_vm_error:
                    raise exceptions.VMIsError(vm=vm.id)
            if timeout and time.time() >= stop_time:
                raise exceptions.WaitVMStatusTimeout(vm=vm.id,
                                                     expect=check_status,
                                                     actual=vm_state)
            LOG.debug('[vm: %s] vm_state=%s, stask_state=%s',
                      vm.id, vm_state, task_state)
            if (not check_status or vm_state in check_status) and \
               (not task_states or task_state in task_states):
                break
            time.sleep(interval)
        return vm

    def clean_vms(self, vms):
        for vm in vms:
            self.delete_vm(vm, wait=True)

    def delete_vm(self, vm, wait=False, ignore_vm_error=False):
        try:
            vm.delete()
            LOG.debug('[vm: %s] deleting', vm.id)
            if wait:
                self._wait_for_vm(vm, status='deleted',
                                  ignore_vm_error=ignore_vm_error)
        except nova_exc.NotFound:
            LOG.debug('[vm: %s] deleted', vm.id)

    def _create_volume(self, wait=False):
        LOG.info('creating volume')
        vol = self.openstack.create_volume(self.generate_name('vol'))
        if not wait:
            return vol
        timeout_exc = exceptions.VolumeCreateTimeout(volume=vol.id,
                                                     timeout=600)
        for w in waiter.loop_waiter(self.openstack.get_volume, args=(vol.id,),
                                    interval=5, timeout=600,
                                    timeout_exc=timeout_exc):
            if w.result.status == 'available':
                w.finish = True
            elif w.result.status == 'error':
                w.finish = True
        return vol

    def _get_vm_ips(self, vm_id):
        ip_list = []
        for vif in self.openstack.list_interface(vm_id):
            ip_list.extend([ip['ip_address'] for ip in vif.fixed_ips])
        return ip_list

    def _get_vm_volume_devices(self, vm):
        device_list = []
        for vol in self.openstack.nova.volumes.get_server_volumes(vm.id):
            device_list.append(vol.device)
        return device_list

    def delete_volumes(self, volumes):
        for vol in volumes:
            self.openstack.delete_volume(vol.id)

    def report_vm_actions(self, vm):
        st = table.SimpleTable()
        vm_actions = self.openstack.get_vm_events(vm)
        vm_actions = sorted(vm_actions, key=lambda x: x[1][0]['start_time'])
        st.set_header([
            'VM', 'Action', 'Event', 'StartTime', 'EndTime', 'Result'])
        for action_name, events in vm_actions:
            for event in events:
                st.add_row([vm.id, action_name, event.get('event') or '',
                            event.get('start_time')  or '',
                            event.get('finish_time')  or '',
                            event.get('result')  or ''])
        LOG.info('[vm: %s] actions:\n%s', vm.id, st.dumps())

    def check_can_migrate(self, vm):
        compute_services = self.get_available_services(binary='nova-compute')
        if len(compute_services) < 2:
            msg = '[vm: %s] can not migrate, because compute services is < 2'
            LOG.warning(colorstr.YellowStr(msg), vm.id)
            return False
        return True

    def get_attach_net(self):
        if not self._attach_net:
            import random
            net, _ = self.create_net_with_subnet(
                '192.168.{}.0/24'.format(random.randint(1, 255)))
            self._attach_net = net.get('id')
        return self._attach_net

    def create_net_with_subnet(self, cidr):
        LOG.info('create network and subnet with cidr %s', cidr)
        net = self.openstack.neutron.create_network({
            'network': {'name': self.generate_name('net')}})
        self.cleanup_manager.add(self.openstack.neutron.delete_network,
                                 net.get('network').get('id'))
        subnet = self.openstack.neutron.create_subnet({
            'subnet': {'name': self.generate_name('subnet'),
                       'network_id': net.get('network').get('id'),
                       'cidr': cidr,
                       "ip_version": 4}
            })
        return net.get('network'), subnet.get('subnet')

    def evacute_vms(self, host, vms=None, wait=False):
        vms = vms or []
        LOG.info('start to test evacuate at %s, vm num is %s',
                    host, len(vms))
        for vm in vms:
            vm.evacuate()
        if not wait:
            return

        bar = progressbar.factory(CONF.task.total)
        with futures.ThreadPoolExecutor(max_workers=CONF.task.worker) as tpe:
            tasks = [tpe.submit(self._wait_for_vm) for _ in range(vms)]
            for future in futures.as_completed(tasks):
                try:
                    vm = future.result()
                    self.report_vm_actions(vm)
                except Exception as e:
                    LOG.exception(e)
                finally:
                    bar.update(1)

    def wait_service_status(self, service, status=None, state=None,
                            timeout=60, interval=1):
        status = status or 'enabled'
        state = state or 'up'
        stop_time = time.time() + timeout if timeout else None
        while True:
            service = self.openstack.nova.services.list(
                host=service.host, binary=service.binary)[0]
            LOG.debug('service %s:%s status=%s, state=%s',
                      service.host, service.binary,
                      service.status, service.state)
            if service.status == status and service.state == state:
                break
            if timeout and time.time() >= stop_time:
                raise exceptions.WaitSerivceStatusTimeout(service=service.id,
                                                          timeout=timeout)
            time.sleep(interval)
        return service


class VMManager(VMManagerBase):

    def cleanup_vms(self, name=None, workers=None, status=None):
        workers = workers or 1
        servers = self.get_deletable_servers(name=name, status=status)
        if not servers:
            return

        LOG.info('delete %s vms ...', len(servers))
        bar = progressbar.factory(len(servers))
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            tasks = [
                executor.submit(self.delete_vm, s, ignore_vm_error=True,
                                wait=True) for s in servers]
            for future in futures.as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    LOG.error(e)
                finally:
                    bar.update(1)
        bar.close()

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
        for params in [(1, 1, 10), (4, 4, 20), (8, 8, 40)]:
            self.create_flavor(name_prefix, params[0], params[1], params[2])

    def create_vm(self, image_id, flavor_id, name=None, nics=None, az=None,
                  min_count=None, max_count=None,
                  create_timeout=1800, wait=False):
        image, block_device_mapping_v2 = None, None
        if CONF.openstack.boot_from_volume:
            block_device_mapping_v2 = [{
                'source_type': 'image', 'uuid': image_id,
                'volume_size': CONF.openstack.volume_size,
                'destination_type': 'volume', 'boot_index': 0,
                'delete_on_termination': True,
            }]
            name = self.generate_name('vol-vm')
        else:
            image = image_id
        if not name:
            name = self.generate_name(
                CONF.openstack.boot_from_volume and 'vol-vm' or 'img-vm')
        vm = self.openstack.nova.servers.create(
            name, image, flavor_id, nics=nics,
            block_device_mapping_v2=block_device_mapping_v2,
            availability_zone=az or CONF.openstack.boot_az,
            min_count=min_count, max_count=max_count,)
        LOG.info('[vm: %s] booting, with %s', vm.id,
                 'bdm' if CONF.openstack.boot_from_volume else 'image')
        if wait:
            try:
                self._wait_for_vm(vm, timeout=create_timeout)
            except exceptions.VMIsError:
                raise exceptions.VmCreatedFailed(vm=vm.id)
            LOG.debug('[vm: %s] created, host is %s',
                      vm.id, getattr(vm, 'OS-EXT-SRV-ATTR:host'))
        return vm

    def wait_for_volume(self, volume_id, status=None):
        if status is None:
            status = ['available']
        interval = 5
        end_time = time.time() + 600
        LOG.info('volume %s waiting for status to be %s', volume_id, status)
        while True:
            vol = self.openstack.get_volume(volume_id)
            if vol.status == 'error':
                raise exceptions.VolumeCreateFailed(volume=volume_id)
            if vol.status == 'available':
                LOG.debug('volume %s is available %s', volume_id, vol.status)
                return vol
            LOG.debug('waiting for volume %s, status is %s',
                      vol.id, vol.status)
            if time.time() > end_time:
                raise exceptions.VolumeCreateTimeout(
                    volume=vol.id, timeout=CONF.task.detach_interface_timeout)
            time.sleep(interval)

    def _test_vm(self):
        nics = self._get_nics()
        vm = self.create_vm(CONF.openstack.image_id, CONF.openstack.flavor_id,
                            nics=nics)
        LOG.info('[vm: %s] (%s) creating', vm.id, vm.name)
        try:
            self._wait_for_vm(vm, timeout=60 * 10)
        except (exceptions.WaitVMStatusTimeout,
                exceptions.VMIsError) as e:
            self.delete_vm(vm)
            raise exceptions.StartFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] created, host: %s'),
                 vm.id, getattr(vm, 'OS-EXT-SRV-ATTR:host'))

        try:
            self.test_interface_attach_detach(vm)
            self.test_volume_attach_detach(vm)
            self.test_stop(vm)
            self.test_suspend(vm)
            self.test_pause(vm)
            self.test_resize(vm)
            self.test_reboot(vm)
            self.test_migrate(vm)
            self.test_live_migrate(vm)
        except Exception as e:
            LOG.exception(e)
            LOG.error(colorstr.RedStr('[vm: %s] test failed, error: %s'),
                      vm.id, e)
        else:
            LOG.info(colorstr.GreenStr('[vm: %s] test success'), vm.id)
        finally:
            self.report_vm_actions(vm)
            self.clean_vms([vm])

    @check_if_skip(constants.STOP)
    def test_stop(self, vm):
        vm.stop()
        LOG.info('[vm: %s] stopping', vm.id)
        try:
            self._wait_for_vm(vm, status='stopped', timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout,
                exceptions.VMIsError) as e:
            raise exceptions.StopFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] stopped'), vm.id)
        vm.start()
        LOG.info('[vm: %s] starting', vm.id)
        try:
            vm = self._wait_for_vm(vm, timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout,
                exceptions.VMIsError) as e:
            raise exceptions.StartFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] started'), vm.id)
        return vm

    @check_if_skip(constants.REBOOT)
    def test_reboot(self, vm):
        vm.reboot()
        LOG.info('[vm: %s] rebooting', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 10, interval=5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.RebootFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] rebooted'), vm.id)
        return vm

    @check_if_skip(constants.SUSPEND)
    def test_suspend(self, vm):
        vm.suspend()
        LOG.info('[vm: %s] suspending', vm.id)
        try:
            self._wait_for_vm(vm, status='suspended', timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.SuspendFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] suspended'), vm.id)
        vm.resume()
        LOG.info('[vm: %s] resuming', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.ResumeFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] resumed'), vm.id)

    @check_if_skip(constants.PAUSE)
    def test_pause(self, vm):
        vm.pause()
        LOG.info('[vm: %s] pasuing', vm.id)
        try:
            self._wait_for_vm(vm, status='paused', timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.ResumeFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] paused'), vm.id)
        vm.unpause()
        LOG.info('[vm: %s] unpasuing', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.ResumeFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] unpaused'), vm.id)

    @check_if_skip(constants.ATTACH_INTERFACE)
    def test_interface_attach_detach(self, vm):
        for t in range(CONF.task.attach_net_times):
            LOG.info('[vm: %s] test interface attach & detach %s', vm.id, t)
            attached_ports = []
            for i in range(CONF.task.attach_net_nums):
                LOG.info('[vm: %s] attach interface %s', vm.id, i + 1)
                attached = vm.interface_attach(None, self.get_attach_net(),
                                               None)
                attached_ports.append(attached.port_id)
            ips = self._get_vm_ips(vm.id)
            LOG.info('[vm: %s] ip address are: %s', vm.id, ips)
            for port_id in attached_ports:
                LOG.info('[vm: %s] detach interface %s', vm.id, port_id)
                self._detach_interface(vm.id, port_id, wait=True)
            ips = self._get_vm_ips(vm.id)
            LOG.info('[vm: %s] ip address are: %s', vm.id, ips)

    def test_volume_attach(self, vm):
        attached_volumes = []
        for i in range(CONF.task.attach_volume_nums):
            vol = self._create_volume(wait=True)
            LOG.info('[vm: %s] attaching volume %s, %s', vol.id, vm.id, i + 1)
            self._attach_volume(vm, vol, wait=True)
            LOG.info('[vm: %s] attached volume %s, %s', vol.id, vm.id, i + 1)
            attached_volumes.append(vol)
        LOG.info(colorstr.GreenStr('[vm: %s] attached %s volume(s)'),
                 vm.id, len(attached_volumes))
        return attached_volumes

    def test_volume_detach(self, vm, attached_volumes):
        for vol in attached_volumes:
            LOG.info('[vm: %s] volume %s detaching', vm.id, vol.id)
            self._detach_volume(vm, vol.id, wait=True)
        LOG.info(colorstr.GreenStr('[vm: %s] detached %s volume(s)'),
                 vm.id, len(attached_volumes))

    @check_if_skip(constants.ATTACH_VOLUME)
    def test_volume_attach_detach(self, vm):
        attached_volumes = []
        for t in range(CONF.task.attach_volume_nums):
            LOG.info('[vm: %s] volume attaching %s', vm.id, t + 1)
            attached_volumes = self.test_volume_attach(vm)
            self.test_volume_detach(vm, attached_volumes)

        vol_devices = self._get_vm_volume_devices(vm)
        LOG.info('[vm: %s] block devices: %s', vm.id, vol_devices)
        LOG.debug('clean up volumes: %s', attached_volumes)
        self.delete_volumes(attached_volumes)

    def _detach_interface(self, vm_id, port_id, wait=False):
        self.openstack.detach_interface(vm_id, port_id)
        if not wait:
            return

        waiter_kwargs = {
            'interval': CONF.task.detach_interface_wait_interval,
            'timeout': CONF.task.detach_interface_wait_timeout,
            'timeout_exc': exceptions.InterfaceDetachTimeout(
                vm=vm_id, timeout=CONF.task.detach_interface_wait_timeout)
        }

        for w in waiter.loop_waiter(self.openstack.nova.servers.interface_list,
                                    args=(vm_id,), **waiter_kwargs):
            for interface in w.result:
                if interface.id == port_id:
                    w.finish = False
                    break
            else:
                w.finish = True

    def _attach_volume(self, vm, volume, wait=False):
        self.openstack.attach_volume(vm.id, volume.id)
        if not wait:
            return
        timeout_exc = exceptions.VolumeAttachTimeout(volume=volume.id,
                                                     timeout=600)
        for w in waiter.loop_waiter(
            self.openstack.cinder.volumes.get, args=(volume.id,),
            interval=5, timeout=600, timeout_exc=timeout_exc):
            if w.result.status == 'in-use':
                w.finish = True
            elif w.result.status == 'error':
                w.finish = True
                raise exceptions.VolumeDetachFailed(volume=volume.id)

    def _detach_volume(self, vm, volume_id, wait=False):
        self.openstack.detach_volume(vm.id, volume_id)
        if not wait:
            return
        timeout_exc = exceptions.VolumeDetachTimeout(volume=volume_id,
                                                     timeout=600)
        for w in waiter.loop_waiter(
                self.openstack.cinder.volumes.get, args=(volume_id,),
                interval=5, timeout=600, timeout_exc=timeout_exc):
            if w.result.status == 'available':
                w.finish = True
            elif w.result.status == 'error':
                w.finish = True
                raise exceptions.VolumeDetachFailed(volume=volume_id)
        LOG.info('[vm: %s] volume %s detached', vm.id, volume_id)

    def test_vm(self):
        invalid_actions = set(CONF.task.vm_test_actions) - \
            set(constants.ACTIONS_ALL)
        if invalid_actions:
            LOG.error('Invalid action(s): %s', ' '.join(invalid_actions))
            return
        LOG.info('start tasks, worker: %s, total: %s, actions: %s',
                 CONF.task.worker, CONF.task.total, CONF.task.vm_test_actions)
        bar = progressbar.factory(CONF.task.total)
        with futures.ThreadPoolExecutor(max_workers=CONF.task.worker) as tpe:
            tasks = [
                tpe.submit(self._test_vm) for _ in range(CONF.task.total)]
            failed = 0
            for future in futures.as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    failed += 1
                    LOG.exception(e)
                finally:
                    bar.update(1)
        bar.close()
        LOG.info('Summary: %(failed)s/%(total)s failed, '
                 '%(success)s/%(total)s success.',
                 {'failed': failed and colorstr.RedStr(failed) or 0,
                  'success': colorstr.GreenStr(CONF.task.total - failed),
                  'total': CONF.task.total})
        self.cleanup_manager.cleanup()

    @check_if_skip(constants.RESIZE)
    def test_resize(self, vm):
        flavor = self._get_flavor(CONF.openstack.flavor_id)
        new_flavor = self.create_flavor(flavor.ram + 1024, flavor.vcpus + 1,
                                        disk=flavor.disk,
                                        metadata=flavor.get_keys())
        LOG.debug('[vm: %s] created new flavor, ram=%s vcpus=%s',
                  vm.id, new_flavor.vcpus, new_flavor.ram)
        vm.resize(new_flavor)
        LOG.info('[vm: %s] resizing', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 10, interval=5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.ResizeFailed(vm=vm.id, reason=e)
        LOG.info(colorstr.GreenStr('[vm: %s] resized'), vm.id)

    @check_if_skip(constants.MIGRATE)
    def test_migrate(self, vm):
        if not self.check_can_migrate(vm):
            return
        src_host = getattr(vm, 'OS-EXT-SRV-ATTR:host')
        vm.migrate()
        LOG.info('[vm: %s] migrating', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 10, interval=5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.MigrateFailed(vm=vm.id, reason=e)
        dest_host= getattr(vm, 'OS-EXT-SRV-ATTR:host')
        if src_host == dest_host:
            raise exceptions.MigrateFailed(
                vm=vm.id, reason='src host and dest host are the same')
        LOG.info(colorstr.GreenStr('[vm: %s] migrated, %s --> %s'),
                 vm.id, src_host, dest_host)

    @check_if_skip(constants.LIVE_MIGRATE)
    def test_live_migrate(self, vm):
        if not self.check_can_migrate(vm):
            return
        src_host = getattr(vm, 'OS-EXT-SRV-ATTR:host')
        vm.live_migrate()
        LOG.info('[vm: %s] live migrating', vm.id)
        try:
            self._wait_for_vm(vm, timeout=60 * 10, interval=5)
        except (exceptions.WaitVMStatusTimeout, exceptions.VMIsError) as e:
            raise exceptions.LiveMigrateFailed(vm=vm.id, reason=e)
        dest_host= getattr(vm, 'OS-EXT-SRV-ATTR:host')
        if src_host == dest_host:
            raise exceptions.LiveMigrateFailed(
                vm=vm.id, reason='src host and dest host are the same')
        LOG.info(colorstr.GreenStr('[vm: %s] live migrated, %s --> %s'),
                 vm.id, src_host, dest_host)

    def test_evacuate(self):
        compute_services = self.get_available_services(binary='nova-compute')
        if len(compute_services) < 2:
            msg = 'can not migrate, because active compute services is < 2'
            LOG.warning(colorstr.YellowStr(msg))
            return
        test_az, test_host = None, None
        vms = []
        if CONF.openstack.boot_az:
            try:
                test_az, test_host = CONF.openstack.boot_az.split(':')
            except:
                LOG.error('Invalid evacuate_az: %s, it must be AZ:HOST',
                          CONF.openstack.evacuate_az)
                return
        else:
            LOG.info('create one vm, and select the host as evacuate host')
            vm = self.create_vm(CONF.openstack.image_id,
                                CONF.openstack.flavor_id,
                                nics=self._get_nics(),
                                wait=True)
            test_az = getattr(vm, 'OS-EXT-AZ:availability_zone')
            test_host = getattr(vm, 'OS-EXT-SRV-ATTR:host')
            vms.append(vm)
            LOG.info('created vm at %s:%s', test_az, test_host)

        LOG.info('prepare other vm(s) at %s:%s', test_az, test_host)
        bar = progressbar.factory(CONF.task.evacuate_vms_num - len(vms))
        with futures.ThreadPoolExecutor(max_workers=CONF.task.worker) as tpe:
            tasks = []
            for _ in range(CONF.task.evacuate_vms_num - len(vms)):
                tasks.append(
                    tpe.submit(self.create_vm, CONF.openstack.image_id,
                               CONF.openstack.flavor_id, nics=self._get_nics(),
                               wait=True))
            for future in futures.as_completed(tasks):
                try:
                    vm = future.result()
                    vms.append(vm)
                except Exception as e:
                    LOG.warning('create vm failed, error=%s', e)
                finally:
                    bar.update(1)
        if len(vms) != CONF.task.evacuate_vms_num:
            LOG.error('there is not enough vms in host %s:%s',
                      test_az, test_host)
            return

        LOG.info('try to force down %s:nova-compute', test_host)
        service = self.openstack.nova.services.list(host=test_host,
                                                    binary='nova-compute')[0]
        self.openstack.force_down(service, True)
        time.sleep(3)
        try:
            self.wait_service_status(service, state='down')
            self.evacute_vms(test_host, vms=vms, wait=True)
        except Exception as e:
            LOG.error(e)
        finally:
            LOG.info('unset force down %s nova-compute', test_host)
            self.openstack.force_down(service, False)
            self.clean_vms(vms)
