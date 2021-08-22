import os

from werkzeug.routing import BaseConverter

from fplib.common import log
from fplib.server import httpserver
from fphttpfs import views

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
