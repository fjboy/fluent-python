import base64
import os
import json
import requests

from fp_lib.common import cliparser
from fp_lib.common import log
from fp_lib import date

LOG = log.getLogger(__name__)


class GiteeDriver(object):

    def __init__(self, userspace, repo, token):
        self.userspace = userspace
        self.repo = repo
        self.token = token
        self.session = requests.Session()

    def upload(self, file_path, remote_dir=None):
        file_name = os.path.basename(file_path)
        remote_path = '{}/{}'.format(remote_dir or self._make_upload_path(),
                                     file_name)
        url = 'https://gitee.com/api/v5/repos/{}/{}/contents/{}'.format(
            self.userspace, self.repo, remote_path)
        data = {
            'access_token': self.token,
            'content': self._base64(file_path),
            'message': 'add file {}'.format(file_name)}
        try:
            resp_data = self._post(url, data)
        except requests.exceptions.HTTPError as e:
            LOG.exception(e)
            raise
        return resp_data

    def _post(self, url, data):
        LOG.debug('post url: %s', url)
        resp = self.session.post(url, data)
        LOG.debug('Resp: %s %s %s',
                  resp.status_code, resp.reason, resp.content)
        resp.raise_for_status()
        return json.loads(resp.content)

    def _base64(self, file_path):
        LOG.debug('base64 encode %s', file_path)
        with open(os.path.abspath(file_path), 'rb') as f:
            base64_data = base64.b64encode(f.read())
        return base64_data

    def _make_upload_path(self):
        return date.now_str(date_format='%Y/%m/%d')


class GiteeUpload(cliparser.CliBase):
    NAME = 'gitee-upload'
    ARGUMENTS = [
        cliparser.Argument('local', nargs='+', help='local files to upload'),
        cliparser.Argument('-u', '--user',  required=True,
                           help='username of gitee'),
        cliparser.Argument('-r', '--repo',  required=True,
                           help='repo name of gitee'),
        cliparser.Argument('-t', '--token',  required=True,
                           help='toek of gitee'),
        cliparser.Argument('--remote', help='remote path'),
        cliparser.Argument('--url', default='https://gitee.com/api/v5',
                           help='api url for gitee'),
    ]

    def __call__(self, args):
        driver = GiteeDriver(args.user, args.repo, args.token)
        for local_file in args.local:
            resp = driver.upload(local_file, remote_dir=args.remote)
            print(resp.get('content', {}).get('download_url'))


def list_sub_commands():
    return [GiteeUpload]
