import argparse
import logging
import os
import sys

from fplib.common import log
from fplib.server import httpserver

from fphttpfs import manager
from fphttpfs import views

LOG = log.getLogger(__name__)
ROUTE = os.path.dirname(os.path.abspath(__file__))


class FluentHttpFS(httpserver.WsgiServer):

    RULES = [
        (r'/favicon.ico', views.FaviconView.as_view('favicon')),
        (r'/', views.HomeView.as_view('home')),
        (r'/index.html', views.IndexView.as_view('index')),
        (r'/action', views.ActionView.as_view('action')),
        (r'/download/<file_name>', views.DownloadView.as_view('download')),
        (r'/qrcode', views.QrcodeView.as_view('qrcode')),
    ]

    def __init__(self, host=None, port=80, fs_root=None):
        super().__init__('FluentHttpFS', host=host, port=port,
                         template_folder=os.path.join(ROUTE, 'templates'),
                         static_folder=os.path.join(ROUTE, 'static'))
        self.fs_root = fs_root or './'
        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        self.driver = manager.FSManager(self.fs_root)
        views.FS_CONTROLLER = manager.FSManager(self.fs_root)


def main():
    parser = argparse.ArgumentParser('Fluent HTTP FS Command')
    parser.add_argument('-d', '--debug', action='store_true',
                        help="show debug message")
    parser.add_argument('-P', '--path', help="the path of backend")
    parser.add_argument('-p', '--port', type=int, default=80,
                        help="the port of server, default 80")
    parser.add_argument('--development', action='store_true',
                        help="run server as development mode")
    args = parser.parse_args()
    if args.debug:
        log.set_default(level=logging.DEBUG)
    server = FluentHttpFS(fs_root=args.path, port=args.port)
    server.start(develoment=args.development, debug=args.debug)


if __name__ == '__main__':
    sys.exit(main())
