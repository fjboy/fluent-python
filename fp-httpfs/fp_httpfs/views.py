import os
import json
import flask

from flask import views
from flask import current_app
from flask.globals import session

from fp_lib.common import log
from fp_lib import fs
from fp_httpfs import manager
from fp_httpfs import auth
import copy

LOG = log.getLogger(__name__)
FS_CONTROLLER = None
AUTH_CONTROLLER = None

SERVER_NAME = 'HttpFS'
VERSION = '1.1 beta'


DEFAULT_CONTEXT = {
    'name': SERVER_NAME,
    'version': manager.get_version()
}


import pbr


def get_json_response(data, status=200):
    return flask.Response(json.dumps(data), status=status,
                          headers={'Content-Type': 'application/json'})


def set_fs_manager(root_path):
    global FS_CONTROLLER
    if not FS_CONTROLLER:
        FS_CONTROLLER = manager.FSManager(root_path)


def set_auth_manager(password):
    global AUTH_CONTROLLER
    if not AUTH_CONTROLLER:
        AUTH_CONTROLLER = auth.AuthManager(password)


def get_resp_context():
    context = copy.deepcopy(DEFAULT_CONTEXT)
    context.update({'username': session.get('username', 'guest')})
    return context


class HomeView(views.MethodView):

    def get(self):
        return flask.redirect('/index.html')


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html', **get_resp_context())


class FaviconView(views.MethodView):

    def get(self):
        return flask.send_from_directory(current_app.static_folder,
                                         'httpfs.png')


class FSView(views.MethodView):

    def get(self, dir_path):
        req_path = dir_path.split('/')[1:]
        usage = FS_CONTROLLER.disk_usage()
        all = flask.request.args.get('all', False)
        try:
            children = FS_CONTROLLER.ls(req_path, all=all)
        except FileNotFoundError:
            return get_json_response({'error': 'file not found'}, status=404)
        return {
            'dir': {
                'path': req_path,
                'children': children,
                'disk_usage': {
                    'used': usage.used, 'total': usage.total
                }
            }
        }

    def delete(self, dir_path):
        req_path = dir_path.split('/')[1:]
        force = flask.request.args.get('force', False)
        FS_CONTROLLER.rm(req_path, force=force)
        return {'result': 'delete success'}

    def post(self, dir_path):
        """Create dir
        POST /fs/foo/bar
        """
        LOG.debug('create path: %s', dir_path)
        req_path = dir_path.split('/')[:]
        if FS_CONTROLLER.path_exists(req_path):
            raise ValueError('path is already exists: %s' % req_path)
        FS_CONTROLLER.mkdir(req_path)
        return {'result': 'create success'}

    def put(self, dir_path):
        """Rename file/directory
        PUT /fs/foo/bar -d '{"dir": {"new_name": "bar2"}}'
        """
        req_path = dir_path.split('/')[1:]
        data = json.loads(flask.request.data)
        new_name = data.get('dir', {}).get('new_name')
        if not new_name:
            return get_json_response({'error': 'new name is none'}, status=400)
        FS_CONTROLLER.rename(req_path, new_name)
        return {'result': 'rename success'}


class FileView(views.MethodView):

    def get(self, dir_path):
        req_path = dir_path.split('/')[1:]
        abs_path = FS_CONTROLLER.get_abs_path(req_path)
        try:
            if FS_CONTROLLER.is_file(req_path):
                directory = os.path.dirname(abs_path)
                send_file = os.path.basename(abs_path)
            else:
                directory = fs.get_tmp_dir()
                send_file = fs.zip_files(abs_path, zip_path=False,
                                         save_path=directory)
            LOG.debug('send file: %s %s', directory, send_file)
            return flask.send_from_directory(directory, send_file,
                                             as_attachment=False)
        except FileNotFoundError as e:
            LOG.exception(e)
            return get_json_response({'error': 'file not found'}, status=404)
        except Exception as e:
            LOG.exception(e)
            return get_json_response({'error': e}, status=500)

    def post(self, dir_path):
        f = flask.request.files.get('file')
        if not f:
            return get_json_response({'error': 'file is null'}, status=401)
        FS_CONTROLLER.save(dir_path.split('/')[1:], f)
        return {'files': {'result': 'file save success'}}


class SearchView(views.MethodView):

    def get(self):
        return {'search': {'history': FS_CONTROLLER.search_history.all()}}

    def post(self):
        """
        params: {'search': {'partern': '*.py'}}
        """
        data = json.loads(flask.request.data)
        partern = data.get('search', {}).get('partern')
        if not partern:
            return get_json_response({'error': 'partern is none'}, status=400)
        matched_pathes = FS_CONTROLLER.find(partern)
        return {'search': {'dirs': matched_pathes}}


class AuthView(views.MethodView):

    def post(self):
        data = flask.request.data
        if not data:
            return get_json_response({'error': 'auth info not found'},
                                     status=400)
        auth = json.loads(data).get('auth', {})
        LOG.debug('auth with: %s', auth)
        if AUTH_CONTROLLER.is_valid(auth.get('username'),
                                    auth.get('password')):
            session['username'] = auth.get('username')
            return get_json_response({}, status=200)
        else:
            return get_json_response({'error': 'auth failed'}, status=401)

    def delete(self):
        session.clear()
        return get_json_response({}, status=204)
