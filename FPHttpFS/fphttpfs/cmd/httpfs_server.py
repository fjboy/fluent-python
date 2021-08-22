import argparse
import logging
import os
import sys

from fplib.common import log
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))     # noqa
from fphttpfs import server                         # noqa


def main():
    parser = argparse.ArgumentParser('Fluent HTTP FS Command')
    parser.add_argument('root', nargs='?',
                        help="the root path of FS")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="show debug message")
    parser.add_argument('-p', '--port', type=int, default=80,
                        help="the port of server, default 80")
    parser.add_argument('--develop', action='store_true',
                        help="run server as development mode")
    args = parser.parse_args()
    if args.debug:
        log.set_default(level=logging.DEBUG)
    fs_server = server.FluentHttpFS(fs_root=args.root, port=args.port)
    fs_server.start(develoment=args.develop, debug=args.debug)


if __name__ == '__main__':
    sys.exit(main())