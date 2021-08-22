import argparse
import logging
import os
import sys

from fplib.common import log
from fplib.server import httpserver

from fphttpfs import views

from werkzeug.routing import BaseConverter

LOG = log.getLogger(__name__)

ROUTE = os.path.dirname(os.path.abspath(__file__))


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class FluentHttpFS(httpserver.WsgiServer):

    RULES = [
        (r'/favicon.ico', views.FaviconView.as_view('favicon')),
        (r'/', views.HomeView.as_view('home')),
        (r'/index.html', views.IndexView.as_view('index')),
        (r'/action', views.ActionView.as_view('action')),
        (r'/fs<regex("/|/.*"):dir_path>', views.FSView.as_view('fs')),
    ]

    def __init__(self, host=None, port=80, fs_root=None):
        super().__init__('FluentHttpFS', host=host, port=port,
                         template_folder=os.path.join(ROUTE, 'templates'),
                         static_folder=os.path.join(ROUTE, 'static'),
                         converters_ext=[('regex', RegexConverter)])
        self.fs_root = fs_root or './'
        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        views.set_fs_manager(self.fs_root)


def main():
    parser = argparse.ArgumentParser('Fluent HTTP FS Command')
    parser.add_argument('-d', '--debug', action='store_true',
                        help="show debug message")
    parser.add_argument('-P', '--path', help="the path of backend")
    parser.add_argument('-p', '--port', type=int, default=80,
                        help="the port of server, default 80")
    parser.add_argument('--develop', action='store_true',
                        help="run server as development mode")
    args = parser.parse_args()
    if args.debug:
        log.set_default(level=logging.DEBUG)
    server = FluentHttpFS(fs_root=args.path, port=args.port)
    server.start(develoment=args.develop, debug=args.debug)


if __name__ == '__main__':
    sys.exit(main())
