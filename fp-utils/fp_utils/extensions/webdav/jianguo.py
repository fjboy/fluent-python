from fp_lib.common import cliparser
from fp_utils.extensions.webdav import base


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
        client = base.WebDavClient(args.url, args.user, args.password)
        for local_file in args.local:
            remote_path = client.upload(local_file, args.remote)
            print(remote_path)


def list_sub_commands():
    return [JianguoUpload]
