import os

from webdav3.client import Client
from webdav3 import exceptions

from fp_lib.common import cliparser
from fp_lib.common import log

LOG = log.getLogger(__name__)


class WebDavClient(object):
    """WebDav client for jianguo cloud

    Create a directory under the root directory of the jianguo cloud first,
    and create a token as password according the instruction:

        https://help.jianguoyun.com/?p=2064.

    then use this client to uplodad file.
    """

    def __init__(self, url, username, password, disable_check=True):
        self.webdav = Client({'webdav_hostname': url,
                              'webdav_login': username,
                              'webdav_password': password,
                              'disable_check': disable_check})

    def upload(self, local_file, remote_dir):
        file_name = os.path.basename(local_file)
        file_path = os.path.abspath(local_file)
        remote_path = '/{}/{}'.format(remote_dir, file_name)
        LOG.debug('upload file %s', file_name)
        try:
            self.webdav.upload(remote_path, file_path)
            LOG.debug('uploaded file %s', file_name)
            return self.webdav.get_url(remote_path)
        except exceptions.LocalResourceNotFound:
            LOG.error('file %s is not found', file_path)
