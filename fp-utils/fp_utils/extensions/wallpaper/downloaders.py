"""wallpaper downloader"""

import importlib

from fp_lib.common import cliparser
from fp_lib.common import log
from fp_lib import system

LOG = log.getLogger(__name__)

UHD_CHOICES = ['only', 'include', 'no']
RESOLUTION_UHD = 'uhd'
RESOLUTION_1920 = '1920x1080'
UHD_CHOICES = ['only', 'include', 'no']
UHD_RESOLUTION_MAPPING = {'include': None,
                          'no': RESOLUTION_1920,
                          'only': RESOLUTION_UHD}

DOWNLOADER = {
    'bingimg': 'fp_utils.extensions.wallpaper.bingimg.Downloader'
}

class BingimgDownload(cliparser.CliBase):
    NAME = 'bingimg-download'
    ARGUMENTS = [
        cliparser.Argument('page', type=int,
                           help='download page begin with'),
        cliparser.Argument('-e', '--end', type=int,
                           help='end page, default is None'),
        cliparser.Argument('-u', '--uhd', default='only', choices=UHD_CHOICES,
                           help='only: only download UHD; '
                                'include: download UHD and other resolutions; '
                                'no: do not download UHD;'),
        cliparser.Argument('-w', '--workers', type=int, default=12,
                           help='the num download workers, default is 12'),
        cliparser.Argument('-t', '--timeout', type=int, default=300,
                           help='timeout, default is 300s'),
        cliparser.Argument('-s', '--save', default='./',
                           help='the directory to save'),
        cliparser.Argument('-n', '--no-progress', action='store_true',
                           help='do not show progress'),
        cliparser.Argument('--wget', action='store_true', help='use wget'),
    ]

    def __call__(self, args):
        if args.wget and system.OS.is_windows():
            LOG.error('Wget is not support in this os')
            return 1
        if args.end and args.end < args.page:
            LOG.error('Invalid value, end page can not lower than start page.')
            return 1

        mod, _, klass = DOWNLOADER['bingimg'].rpartition('.')
        module = importlib.import_module(mod)
        manager_cls = getattr(module, klass)
        manager = manager_cls(progress=not args.no_progress,
                              download_dir=args.save, workers=args.workers,
                              timeout=args.timeout, use_wget=args.wget)

        for page in range(args.page, (args.end or args.page) + 1):
            manager.download(page,
                            resolution=UHD_RESOLUTION_MAPPING[args.uhd])


def list_sub_commands():
    return [BingimgDownload]
