from __future__ import print_function
import os

from keystoneauth1.identity import v3
from keystoneauth1.session import Session
from keystoneclient.v3 import client
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient
import glanceclient

from fplib.common import log

LOG = log.getLogger(__name__)

NOVA_API_VERSION = "2.1"
nova_extensions = [ext for ext in
                   novaclient.discover_extensions(NOVA_API_VERSION)
                   if ext.name in ("assisted_volume_snapshots",
                                   "list_extensions",
                                   "server_external_events")]

class OpenstackClient:

    def __init__(self, *args, **kwargs):
        self.auth = v3.Password(*args, **kwargs)
        self.session = Session(auth=self.auth)
        self.keystone = client.Client(session=self.session)
        self.neutron = neutronclient.Client(session=self.session)
        self.nova = novaclient.Client('2.1', session=self.session,
                                      extensions=nova_extensions)
        self.glance = glanceclient.Client(2.1, session=self.session)

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
