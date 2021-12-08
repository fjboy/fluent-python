"""
openstack client
"""
import os

from cinderclient import client as cinder_client
import glanceclient
from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneclient.v3 import client
from neutronclient.v2_0 import client as neutron_client
import novaclient
from novaclient import client as nova_client

from fp_lib.common import exceptions as fp_exc
from fp_lib.common import log

LOG = log.getLogger(__name__)

NOVA_API_VERSION = "2.49"
nova_extensions = [ext for ext in
                   nova_client.discover_extensions(NOVA_API_VERSION)
                   if ext.name in ("assisted_volume_snapshots",
                                   "list_extensions",
                                   "server_external_events")]


class Keystone(object):

    def __init__(self, *args, **kwargs):
        self.auth = v3.Password(*args, **kwargs)
        self.session = Session(auth=self.auth)
        self.keystone = client.Client(session=self.session)

    def get_or_create_domain(self, name):
        domains = self.keystone.domains.list(name=name)
        return domains[0] if domains else self.keystone.domains.create(name)

    def get_or_create_role(self, name, domain_name=None):
        domain = None
        if domain_name:
            domain = self.get_or_create_domain(domain_name)
        roles = self.keystone.roles.list(name=name, domain=domain)
        return roles[0] if roles else self.keystone.roles.create(
            name, domain=domain)

    def get_or_create_project(self, name, domain_name, **kwargs):
        domain = self.get_or_create_domain(domain_name)
        projects = self.keystone.projects.list(name=name, domain=domain)
        return projects[0] if projects else self.keystone.projects.create(
            name, domain, **kwargs)

    def get_or_create_user(self, name, domain_name, projec_name, **kwargs):
        domain = self.get_or_create_domain(domain_name)
        project = self.get_or_create_project(projec_name, domain_name)
        role_name = kwargs.pop('role_name', None)
        users = self.keystone.users.list(name=name, domain=domain)
        user = users[0] if users else self.keystone.users.create(
            name, domain=domain, project=project, **kwargs
        )

        if role_name:
            role = self.get_or_create_role(role_name)
            self.keystone.roles.grant(role, user=user, project=project)
        return user

    def get_quota(self):
        project_id = self.session.get_project_id()
        return self.nova.quotas.get(project_id)


class OpenstackClient(Keystone):
    V3_AUTH_KWARGS = ['username', 'password', 'project_name',
                      'user_domain_name', 'project_domain_name']

    def __init__(self, *args, **kwargs):
        super(OpenstackClient, self).__init__(*args, **kwargs)
        self.neutron = neutron_client.Client(session=self.session)
        self.nova = nova_client.Client(NOVA_API_VERSION,
                                       session=self.session,
                                       extensions=nova_extensions)
        self.glance = glanceclient.Client('2', session=self.session)
        self.cinder = cinder_client.Client('2', session=self.session)

    @classmethod
    def get_auth_info_from_env(cls):
        if 'OS_AUTH_URL' not in os.environ:
            raise fp_exc.EnvIsNone('OS_AUTH_URL')
        auth_url = os.getenv('OS_AUTH_URL')
        auth_kwargs = {}
        for auth_arg in cls.V3_AUTH_KWARGS:
            env = 'OS_{}'.format(auth_arg.upper())
            value = os.getenv(env)
            if not value:
                raise fp_exc.EnvIsNone(env)
            auth_kwargs[auth_arg] = value
        return auth_url, auth_kwargs

    @classmethod
    def create_instance(cls):
        auth_url, auth_kwargs = cls.get_auth_info_from_env()
        LOG.debug('auth info: %s', auth_kwargs)
        return OpenstackClient(auth_url, **auth_kwargs)

    def attach_interface(self, net_id=None, port_id=None):
        return self.nova.servers.interface_attach(net_id=net_id,
                                                  port_id=port_id)

    def detach_interface(self, vm_id, port_id):
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

    def force_down(self, service, force_down):
        if self.nova.api_version >= novaclient.api_versions.APIVersion('2.53'):
            self.nova.services.force_down(service.id, force_down)
        else:
            self.nova.services.force_down(service.host, service.binary,
                                          force_down=force_down)
