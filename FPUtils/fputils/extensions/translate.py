from __future__ import print_function
import argparse
import sys

import translate

from fplib.common import cliparser as cp
from fplib.common import log

LOG = log.getLogger(__name__)

DEFAULT_FROM = 'english'
DEFAULT_TO = 'chinese'


class GoogleTranslate(cp.CliBase):
    NAME = 'google-trans'
    ARGUMENTS = [
        cp.Argument('infile', nargs='?', type=argparse.FileType(),
                    help='A text file be validated or printed'),
        cp.Argument('-f', '--from-language', default=DEFAULT_FROM,
                    help='From language, default is {}'.format(DEFAULT_FROM)),
        cp.Argument('-t', '--to-language', default=DEFAULT_TO,
                    help='To language, default is {}'.format(DEFAULT_TO)),
        cp.Argument('-c', '--chars', type=int, default=500,
                    help='The num of chars each time. default is 500'),
    ]

    def __call__(self, args):
        input = args.infile or sys.stdin
        translactor = translate.Translator(args.to_languate,
                                           from_lang=args.from_languate)
        hint = args.chars
        lines = input.readlines(hint)
        while lines:
            LOG.debug('translate lines: %s', lines)
            text = translactor.translate(''.join(lines))
            if len(text) > 500:
                LOG.warn('The string length is %s, exceeds 500, %s',
                         len(text), text)
                break
            result = translactor.translate(text)
            print(result)
            lines = input.readlines(hint)


def list_sub_commands():
    return [GoogleTranslate]
