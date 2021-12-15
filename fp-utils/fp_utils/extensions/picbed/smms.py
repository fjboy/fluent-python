import os
import requests
import json

from fp_lib.common import cliparser
from fp_utils.extensions.webdav import base


URL = 'https://sm.ms/api/v2'


class SMMSClient(object):

    def __init__(self, username, password, base_url=None):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.base_url = base_url or URL

    def post(self, url, data=None, files=None, headers=None):
        resp = self.session.post('{}{}'.format(self.base_url, url),
                                 data=data, headers=headers, files=files)
        try:
            return json.loads(resp.content)
        except:
            return resp.content

    def login(self):
        data = {'username': self.username, 'password': self.password}
        resp = self.post('/token', data)
        if not resp.get('success'):
            raise Exception('login failed')
        token = resp.get('data').get('token')
        self.token = token

    def upload(self, file_path):
        if not self.token:
            raise Exception('token is none')
        headers = {'Authorization': self.token}
        files = {'smfile': open(file_path, 'rb+')}
        resp = self.post('/upload', headers=headers, files=files)
        if not resp.get('success'):
            raise Exception('upload failed')
        return resp.get('data', {}).get('url')


class SMMSUpload(cliparser.CliBase):
    NAME = 'smms-upload'
    ARGUMENTS = [
        cliparser.Argument('local', nargs='+', help='local files to upload'),
        cliparser.Argument('-u', '--user',  required=True,
                           help='username of jianguo webdav'),
        cliparser.Argument('-p', '--password',  required=True,
                           help='password of jianguo webdav'),
        cliparser.Argument('--url', default='https://sm.ms/api/v2',
                           help='webdav url for jianguo cloud'),
    ]

    def __call__(self, args):
        client = SMMSClient(args.user, args.password, base_url=args.url)
        client.login()
        for local_file in args.local:
            file_url = client.upload(local_file)
            print(file_url)


def list_sub_commands():
    return [SMMSUpload]
