from __future__ import print_function
import argparse
import json
import os
import sys
import io

from fp_lib.common import cliparser
from fp_lib.common import log
from fp_lib.common import jsonobj
from fp_lib import code as code_function
from fp_lib.common import progressbar

LOG = log.getLogger(__name__)


def print_error(message):
    print('Error:', message)
    return 1


class Md5Sum(cliparser.CliBase):
    NAME = 'md5sum'
    ARGUMENTS = [
        cliparser.Argument('file', help='The path of file'),
        cliparser.Argument('-s', '--sha1', action='store_true',
                           help='Calculte sha1 too'),
        cliparser.Argument('--silence', action='store_true',
                           help='DO not show progress'),
        cliparser.Argument('-b', '--buffer', type=int,
                           help='Buffer size, default is {}'.format(
                               io.DEFAULT_BUFFER_SIZE)),
    ]

    def __call__(self, args):
        progress = not args.silence
        if progress and not progressbar.is_support_tqdm:
            LOG.warn('module tpdm is not installed, set progress False')
            progress = False
        if not os.path.exists(args.file):
            print_error('File {} not exists'.format(args.file))
            return 1
        _md5sum, _sha1 = code_function.md5sum_file(args.file,
                                                   sha1=args.sha1,
                                                   read_bytes=args.buffer,
                                                   progress=progress)
        print('md5sum', _md5sum)
        if args.sha1:
            print('sha1  ', _sha1)


class JsonGet(cliparser.CliBase):
    NAME = 'json-get'
    ARGUMENTS = [
        cliparser.Argument('infile', nargs='?', type=argparse.FileType(),
                           help='A JSON file to be validated'),
        cliparser.Argument('-k', '--keys',
                           help='A string of keys, e.g. key1.key2.1'),
        cliparser.Argument('-l', '--lines', action='store_true',
                           help='print as lines'),
        cliparser.Argument('-p', '--pretty', action='store_true',
                           help='Print pretty json'),
    ]

    def __call__(self, args):
        infile = args.infile or sys.stdin
        json_obj = None
        with infile:
            try:
                json_obj = jsonobj.read(infile)
            except json.decoder.JSONDecodeError as e:
                print_error(e)
                return 0
        LOG.debug('keys is %s, pretty is %s', args.keys, args.pretty)
        result = None
        try:
            result = json_obj.get(args.keys) if args.keys else json_obj._value
        except KeyError as e:
            return print_error("Invalid key {}".format(e))
        except ValueError as e:
            return print_error("Invalid index {}".format(e))
        if args.lines and isinstance(result, dict):
            # print as lines
            for key in result:
                print('{} = {}'.format(key, result.get(key)))
        else:
            # print as json
            print(json.dumps(result, indent=args.pretty and '    ' or None))


class GeneratePassword(cliparser.CliBase):
    NAME = 'generate-password'
    ARGUMENTS = [
        cliparser.Argument('infile', nargs='?', type=argparse.FileType(),
                           help='A JSON file to be validated'),
        cliparser.Argument('-l', '--lower', type=int, default=8,
                           help='The num of lower char, default is 8'),
        cliparser.Argument('-u', '--upper', type=int,
                           help='The num of upper char'),
        cliparser.Argument('-n', '--number', type=int,
                           help='The num of number char'),
        cliparser.Argument('-s', '--special', type=int,
                           help='The num of special char'),
    ]

    def __call__(self, args):
        password = code_function.random_password(lower=args.lower,
                                                 upper=args.upper,
                                                 number=args.number,
                                                 special=args.special)
        print(password)
