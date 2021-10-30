from __future__ import print_function
import os
from datetime import datetime
import time
import json

from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneclient import auth
from keystoneclient.v3 import client
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient
import glanceclient

from fp_lib.common import exceptions as fpexc
from fp_lib.common import log

LOG = log.getLogger(__name__)

NOVA_API_VERSION = "2.1"
nova_extensions = [ext for ext in
                   novaclient.discover_extensions(NOVA_API_VERSION)
                   if ext.name in ("assisted_volume_snapshots",
                                   "list_extensions",
                                   "server_external_events")]


class OpenstackClient(object):
    V3_AUTH_KWARGS = ['username', 'password', 'project_name',
                      'user_domain_name', 'project_domain_name']

    def __init__(self, *args, **kwargs):
        self.auth = v3.Password(*args, **kwargs)
        self.session = Session(auth=self.auth)
        self.keystone = client.Client(session=self.session)
        self.neutron = neutronclient.Client(session=self.session)
        self.nova = novaclient.Client('2.1', session=self.session,
                                      extensions=nova_extensions)
        self.glance = glanceclient.Client(2.1, session=self.session)

    @classmethod
    def get_auth_info_from_env(cls):
        if 'OS_AUTH_URL' not in os.environ:
            raise fpexc.EnvIsNone('OS_AUTH_URL')
        auth_url = os.getenv('OS_AUTH_URL')
        auth_kwargs = {}
        for auth_arg in cls.V3_AUTH_KWARGS:
            env = 'OS_{}'.format(auth_arg.upper())
            value = os.getenv(env)
            if not value:
                raise fpexc.EnvIsNone(env)
            auth_kwargs[auth_arg] = value
        return auth_url, auth_kwargs

    @classmethod
    def create_instance(cls):
        auth_url, auth_kwargs = cls.get_auth_info_from_env()
        LOG.debug('auth info: %s', auth_kwargs)
        return OpenstackClient(auth_url, **auth_kwargs)

    @staticmethod
    def generate_vm_name():
        prefix = os.getenv('NOVA_VM_PREFIX', 'test-vm')
        return '{}-{}'.format(prefix, datetime.now().strftime('%m%d-%H:%M:%S'))

    def _wait_for_vm(self, vm_id, status={'active', 'error'}, timeout=None):
        if status:
            check_status = status if isinstance(status, set) else set([status])
        else:
            check_status = []
        task_spend = {}
        timeout_seconds = time.time() + timeout if timeout else None
        while True:
            if timeout_seconds and time.time() > timeout_seconds:
                break
            vm = self.nova.servers.get(vm_id)
            vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
            LOG.debug('vm %s status is %s', vm_id, vm_state)
            if check_status and vm_state in check_status:
                break
            task_state = getattr(vm, 'OS-EXT-STS:task_state')
            if task_state not in task_spend:
                task_spend[task_state] = 1
            else:
                task_spend[task_state] += 1
            time.sleep(1)
        LOG.info('vm %s tasks: %s', vm.id, json.dumps(task_spend, indent=4))
        return vm

    def create_vm(self, image_id, flavor_id, name=None, , nics=None,
                  create_timeout=1800, wait=False):
        start_time = time.time()
        vm = self.nova.servers.create(name=name or self.generate_vm_name(),
                                      image=image_id, flavor=flavor_id,
                                      nics=nics)
        LOG.info('creating vm: %s(%s)', vm.id, vm.name)
        if wait:
            vm = self._wait_for_vm(vm.id, timeout=create_timeout)
        if getattr(vm, 'OS-EXT-STS:vm_state') == 'error':
            LOG.error('vm %s create failed', vm.id)
        else:
            LOG.info('vm %s create success, spend: %.4f seconds',
                     vm.id, time.time() - start_time)
        return vm

    def delete_vm(self, vm_id):
        LOG.info('deleting vm: %s', vm_id)
        self.nova.servers.delete(vm_id)
        try:
            self._wait_for_vm(vm_id, status='deleted')
        except novaclient.exceptions.NotFound:
            pass
        LOG.info('deleted vm: %s', vm_id)
