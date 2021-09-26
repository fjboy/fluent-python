from __future__ import print_function
import time
import os

from fp_lib.common import cliparser
from fp_lib.common import log
from fp_lib import fs

LOG = log.getLogger(__name__)


class PyTac(cliparser.CliBase):
    NAME = 'py-tac'
    ARGUMENTS = [
        cliparser.Argument('file', help='file'),
        cliparser.Argument('-c', '--chunk', type=int, default=None,
                           help='The chunk size to read, default is None'),
        cliparser.Argument('-n', '--nums', type=int, default=None,
                           help='Print Last N lines')]

    def __call__(self, args):
        start_time = time.time()
        nums = args.nums
        if nums is not None and nums <= 0:
            LOG.error('The value of --nums NUM must >= 1')
            return
        with fs.open_backwards(args.file, chunk_size=args.chunk) as fp:
            for line in fp:
                print(line, end='')
                if nums is not None:
                    nums -= 1
                    if nums <= 0:
                        break
        LOG.debug('file is closed: %s', fp.closed)
        LOG.debug('Used Time: %.2f seconds', time.time() - start_time)


class PyZip(cliparser.CliBase):
    NAME = 'zip'
    ARGUMENTS = [
        cliparser.Argument('dir', help='the path of dir'),
        cliparser.Argument('--no-root', action='store_true',
                           help='zip the child of dir'),
        cliparser.Argument('--no-path', action='store_true',
                           help='save path to zip file'),
    ]

    def __call__(self, args):
        try:
            fs.zip_files(args.dir, zip_root=not args.no_root,
                         zip_path=not args.no_path,
                         verbose=args.verbose)
        except FileExistsError:
            LOG.error('%s is not exists', args.dir)
        except Exception as e:
            LOG.error(e)
