from __future__ import print_function
import argparse

from fplib.common import cliparser
from fplib.common import log
from fplib.common import confparser

LOG = log.getLogger(__name__)


class ConfigList(cliparser.CliBase):
    NAME = 'conf-list'
    ARGUMENTS = [
        cliparser.Argument('file', type=argparse.FileType(),
                           help='The path of file'),
        cliparser.Argument('section', nargs='?',
                           help='Section name'),
    ]

    def __call__(self, args):
        LOG.debug(args)
        parser = confparser.ConfigParserWrapper()
        parser.read(args.file)
        if args.section:
            for opt, val in parser.options(args.section,
                                           ignore_default=True).items():
                print(opt, '=', val)
        else:
            print('[{}]'.format('DEFAULT'))
            for opt, val in parser.options('DEFAULT').items():
                print(opt, '=', val)
            print()
            for section in parser.sections():
                print('[{}]'.format(section))
                for opt, val in parser.options(section,
                                            ignore_default=True).items():
                    print(opt, '=', val)
                print()
