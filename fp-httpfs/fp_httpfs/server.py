import os

import flask
from flask import session
from werkzeug.routing import BaseConverter

from fp_lib.common import log
from fp_lib.server import httpserver

from fp_httpfs import views

LOG = log.getLogger(__name__)
ROUTE = os.path.dirname(os.path.abspath(__file__))


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class FluentHttpFS(httpserver.WsgiServer):

    RULES = [
        (r'/', views.HomeView.as_view('home')),
        (r'/favicon.ico', views.FaviconView.as_view('favicon')),
        (r'/auth', views.AuthView.as_view('auth')),
        (r'/index.html', views.IndexView.as_view('index')),
        (r'/fs<regex("/|/.*"):dir_path>', views.FSView.as_view('fs')),
        (r'/file<regex("/|/.*"):dir_path>',
            views.FileView.as_view('file')),
        (r'/search', views.SearchView.as_view('search')),
    ]

    def __init__(self, host=None, port=80, fs_root=None, password=None):
        if password:
            LOG.info('auth request before request')
            self.before_request = self.auth_all_request
        super(FluentHttpFS, self).__init__(
            'FluentHttpFS', host=host, port=port,
            template_folder=os.path.join(ROUTE, 'templates'),
            static_folder=os.path.join(ROUTE, 'static'),
            converters_ext=[('regex', RegexConverter)],
            secret_key='fphttpfs-server-secret-key')
        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        self.fs_root = fs_root or '.'
        self.app.config['admin_password'] = password
        views.set_fs_manager(self.fs_root)
        views.set_auth_manager(password)

    def auth_all_request(self):
        if flask.request.path.startswith('/static') or \
           flask.request.path.startswith('/login') or \
           flask.request.path.startswith('/auth'):
            return
        LOG.debug('session username is %s', session.get('username'))
        if not session.get('username'):
            return flask.render_template('login.html')
