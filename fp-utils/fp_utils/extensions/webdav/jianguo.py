import os

from webdav3.client import Client
from webdav3 import exceptions

from fp_lib.common import cliparser
from fp_lib.common import log

LOG = log.getLogger(__name__)


class WebDavAuth(object):

    def __init__(self, username, password, token):
        self.username = username
        self.password = password
        self.token = token


class JianguoWebDavClient(WebDavAuth):
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


class JianguoUpload(cliparser.CliBase):
    NAME = 'jianguo-upload'
    ARGUMENTS = [
        cliparser.Argument('local', nargs='+', help='local files to upload'),
        cliparser.Argument('-r', '--remote', required=True,
                           help='remote path to save'),
        cliparser.Argument('-u', '--user',  required=True,
                           help='username of jianguo webdav'),
        cliparser.Argument('-p', '--password',  required=True,
                           help='password of jianguo webdav'),
        cliparser.Argument('--url', default='https://dav.jianguoyun.com/dav',
                           help='webdav url for jianguo cloud'),
    ]

    def __call__(self, args):
        client = JianguoWebDavClient(args.url,
                                     args.user, args.password)
        for local_file in args.local:
            remote_path = client.upload(local_file, args.remote)
            print(remote_path)


def list_sub_commands():
    return [JianguoUpload]
