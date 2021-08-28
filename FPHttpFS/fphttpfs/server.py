import os

import flask
from flask import session
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
        (r'/auth', views.AuthView.as_view('auth')),
        (r'/favicon.ico', views.FaviconView.as_view('favicon')),
        (r'/', views.HomeView.as_view('home')),
        (r'/index.html', views.IndexView.as_view('index')),
        (r'/action', views.ActionView.as_view('action')),
        (r'/fs<regex("/|/.*"):dir_path>', views.FSView.as_view('fs')),
        (r'/download<regex("/|/.*"):dir_path>',
            views.DownloadView.as_view('download')),
        (r'/search', views.SearchView.as_view('search')),
    ]

    def __init__(self, host=None, port=80, fs_root=None):
        super().__init__('FluentHttpFS', host=host, port=port,
                         template_folder=os.path.join(ROUTE, 'templates'),
                         static_folder=os.path.join(ROUTE, 'static'),
                         converters_ext=[('regex', RegexConverter)],
                         secret_key='fphttpfs-server-secret-key')
        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        self.fs_root = fs_root or '.'
        views.set_fs_manager(self.fs_root)

    def before_request(self):
        if flask.request.path.startswith('/static') or \
           flask.request.path.startswith('/login') or \
           flask.request.path.startswith('/auth'):
            return
        if not session.get('username'):
            return flask.render_template('login.html')
