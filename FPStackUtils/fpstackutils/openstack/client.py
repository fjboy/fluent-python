"""
openstack client
"""
from __future__ import print_function
import os
import time
import json

from cinderclient import client as cinder_client
import glanceclient
from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneclient.v3 import client
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient

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
        self.cinder = cinder_client.Client('2', session=self.session)

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

    def delete_vm(self, vm):
        vm.delete()

    def attach_interface(self, net_id=None, port_id=None):
        return self.nova.servers.interface_attach(net_id=net_id,
                                                  port_id=port_id)

    def detach_interface(self, vm_id, port_id, wait=True):
        return self.nova.servers.interface_detach(vm_id, port_id)

    def list_interface(self, vm_id):
        return self.nova.servers.interface_list(vm_id)

    def attach_volume(self, vm_id, volume_id):
        return self.nova.volumes.create_server_volume(vm_id, volume_id)

    def detach_volume(self, vm_id, volume_id):
        return self.nova.volumes.delete_server_volume(vm_id, volume_id)

    def create_volume(self, name, size_gb=None):
        size = size_gb or 1
        return self.cinder.volumes.create(size, name=name)

    def get_volume(self, volume_id):
        return self.cinder.volumes.get(volume_id)

    def delete_volume(self, volume_id):
        return self.cinder.volumes.delete(volume_id)

    def get_vm_actions(self, vm):
        actions = {}
        for action in self.nova.instance_action.list(vm.id):
            actions.setdefault(action.action, [])
            vm_action = self.nova.instance_action.get(vm.id,
                                                      action.request_id)
            for event in vm_action.events:
                actions[action.action].append(event)
        return actions

    def get_vm_events(self, vm):
        action_events = []
        for action in self.nova.instance_action.list(vm.id):
            vm_action = self.nova.instance_action.get(vm.id,
                                                      action.request_id)
            events = sorted(vm_action.events,
                            key=lambda x: x.get('start_time'))
            action_events.append((action.action, events))
        return action_events
