from __future__ import print_function
import os
from pickle import NONE

from keystoneauth1.identity import v3
from keystoneauth1.session import Session
import keystoneclient
from keystoneclient.v3 import client
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient
import glanceclient

from fp_lib.common import log

LOG = log.getLogger(__name__)

NOVA_API_VERSION = "2.1"
nova_extensions = [ext for ext in
                   novaclient.discover_extensions(NOVA_API_VERSION)
                   if ext.name in ("assisted_volume_snapshots",
                                   "list_extensions",
                                   "server_external_events")]

class OpenstackClient(object):

    def __init__(self, *args, **kwargs):
        self.auth = v3.Password(*args, **kwargs)
        self.session = Session(auth=self.auth)
        self.keystone = client.Client(session=self.session)
        self.neutron = neutronclient.Client(session=self.session)
        self.nova = novaclient.Client('2.1', session=self.session,
                                      extensions=nova_extensions)
        self.glance = glanceclient.Client(2.1, session=self.session)

    def create_service_endpoints(self, name, service, region,
                                 admin, internal, public,
                                 description=None):
        found = self.keystone.services.list(name=name, type=service)
        if found:
            LOG.warning('service %s(type=%s) exists', name, service)
            service = found[0]
        else:
            service = self.keystone.services.create(name, type=service,
                                                    description=description)

        endpoints = self.keystone.endpoints.list(service=service)
        for endpoint in endpoints:
            LOG.warning('delete endpoint %s', endpoint)
            self.keystone.endpoints.delete(endpoint)

        self.keystone.endpoints.create(service.id, admin, interface='admin',
                                       region=region)
        self.keystone.endpoints.create(service.id, internal, 
                                       interface='internal', region=region)
        self.keystone.endpoints.create(service.id, public, interface='public',
                                       region=region)

    def create_user(self, username, password, project, domain=None, role=None):
        users = self.keystone.users.list(name=username)
        if not users:
            user_obj = self.keystone.users.create(username, domain=domain,
                                                  project=project,
                                                  password=password)
        else:
            user_obj = users[0]
        projects = self.keystone.projects.list(name=project)
        if not projects:
            project_obj= self.keystone.projects.create(project, domain)
        else:
            project_obj = projects[0]

        if not role:
            return
        roles = self.keystone.roles.list(name=role)
        if not roles:
            role_obj = self.keystone.roles.create(role)
        else:
            role_obj = roles[0]

        self.keystone.roles.grant(role_obj.id, user=user_obj.id,
                                  project=project_obj.id)

    @classmethod
    def create_instance(cls):
        if 'OS_AUTH_URL' not in os.environ:
            raise Exception('please source env file.')
        auth_url = os.getenv('OS_AUTH_URL')
        kwargs = dict(
            username=os.getenv('OS_USERNAME'),
            password=os.getenv('OS_PASSWORD'),
            project_name=os.getenv('OS_PROJECT_NAME'),
            user_domain_name=os.getenv('OS_USER_DOMAIN_NAME'),
            project_domain_name=os.getenv('OS_PROJECT_DOMAIN_NAME'),
        )
        LOG.debug('auth info: %s', kwargs)
        return OpenstackClient(auth_url, **kwargs)
