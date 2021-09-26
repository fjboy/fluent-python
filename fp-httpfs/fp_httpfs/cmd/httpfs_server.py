import argparse
import logging
import os
import sys
import mimetypes

from fp_lib.common import log

from fp_httpfs import server


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
    parser.add_argument('--password',
                        help="the password for admin")
    args = parser.parse_args()
    if args.debug:
        log.set_default(level=logging.DEBUG)

    # NOTE(zbw) For windows host, MIME type of js file be
    # 'text/plain', so add this type before start http server.
    mimetypes.add_type('application/javascript', '.js')

    fs_server = server.FluentHttpFS(fs_root=args.root, port=args.port,
                                    password=args.password)
    fs_server.start(develoment=args.develop, debug=args.debug)


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
