import os
import json
import flask

from six.moves import urllib_parse

from flask import views
from flask import current_app

from fplib.common import log
from fplib import fs

import manager

LOG = log.getLogger(__name__)
FS_CONTROLLER = None

SERVER_NAME = 'FluentHttpFS'
VERSION = 1.0

DEFAULT_CONTEXT = {
    'name': SERVER_NAME,
    'version': VERSION
}


def get_json_response(data, status=200):
    return flask.Response(json.dumps(data), status=status,
                          headers={'Content-Type': 'application/json'})


def set_fs_manager(root_path):
    global FS_CONTROLLER
    if not FS_CONTROLLER:
        FS_CONTROLLER = manager.FSManager(root_path)



class HomeView(views.MethodView):

    def get(self):
        return flask.redirect('/index.html')


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html', **DEFAULT_CONTEXT)


class ActionView(views.MethodView):

    ACTION_MAP = {
        'upload_file': 'upload_file',
        'search': 'search',
    }

    def post(self):
        action = flask.request.form.get('action')
        if action:
            action = json.loads(action)
        else:
            action = json.loads(
                flask.request.get_data() or '{}').get('action')
        if not action:
            msg = 'action not found in body'
            return get_json_response({'error': msg}, status=400)

        name = action.get('name')
        params = action.get('params')
        LOG.debug('request action: %s, %s', name, params)
        if name not in self.ACTION_MAP:
            msg = 'action {} is not supported'.format(name)
            return get_json_response({'error': msg}, status=400)
        try:
            resp_body = getattr(self, name)(params)
            return resp_body
        except Exception as e:
            LOG.exception(e)
            return get_json_response({'error': str(e)}, status=400)

    def upload_file(self, params):
        f = flask.request.files.get('file')
        if not f:
            return get_json_response({'error': 'file is null'})
        FS_CONTROLLER.save_file(params.get('path_list'), f)
        return {'result': 'file save success'}

    def _check_params(self, params):
        req_path = params.get('path') or params.get('path_list')

        if not req_path:
            raise ValueError('path is None')
        if req_path and not FS_CONTROLLER.path_exists(req_path):
            raise ValueError('path is not exists: %s' % req_path)

    def search(self, params):
        """
        params: {'partern': '*.py'}
        """
        matched_pathes = []
        if params.get('partern'):
            for p in FS_CONTROLLER.search(params.get('partern')):
                matched_pathes.append(p)
            matched_pathes = FS_CONTROLLER.search(params.get('partern'))
        return {'dirs': matched_pathes}

    def download(self, params):
        """
        params: {'path_list': [] , 'file': 'yy'}
        """
        pass


class FaviconView(views.MethodView):

    def get(self):
        return flask.send_from_directory(current_app.static_folder,
                                         'httpfs.png')


class FSView(views.MethodView):

    def get(self, dir_path):
        req_path = dir_path.split('/')[1:]
        all = flask.request.args.get('all', False)
        usage = FS_CONTROLLER.disk_usage()
        if FS_CONTROLLER.is_file(req_path):
            return self.send_file(req_path)
        try:
            children = FS_CONTROLLER.get_dirs(req_path, all=all)
        except FileNotFoundError:
            return get_json_response({'error': 'file not found'}, status=404)
        for child in children:
            child['pardir'] = req_path
        return {
            'dir': {
                'path': req_path,
                'children': children,
                'disk_usage': {
                    'used': usage.used, 'total': usage.total
                }
            }
        }

    def send_file(self, file_path):
        abs_path = FS_CONTROLLER.get_abs_path(file_path)
        LOG.debug('send file %s', abs_path)
        try:
            directory = os.path.dirname(abs_path)
            return flask.send_from_directory(
                directory, os.path.basename(abs_path), as_attachment=False)
        except FileNotFoundError:
            return get_json_response({'error': 'file not found'}, status=404)
        except Exception as e:
            LOG.exception(e)
            return get_json_response({'error': 'file read failed'}, status=403)

    def download_dir(self, dir_path):
        abs_path = FS_CONTROLLER.get_abs_path(dir_path)
        zip_name = fs.zip_path(abs_path)
        if not os.path.exists(zip_name):
            return get_json_response({'error': 'zip failed'}, status=400)

        LOG.debug('download dir %s', dir_path)
        return flask.send_from_directory('./', zip_name, as_attachment=False)

    def delete(self, dir_path):
        req_path = dir_path.split('/')[1:]
        force = flask.request.args.get('force', False)
        FS_CONTROLLER.delete_dir(req_path, force=force)
        return {'result': 'delete success'}

    def post(self, dir_path):
        """Create dir
        POST /fs/foo/bar
        """
        LOG.debug('create path: %s', dir_path)
        req_path = dir_path.split('/')[:]
        if FS_CONTROLLER.path_exists(req_path):
            raise ValueError('path is already exists: %s' % req_path)
        FS_CONTROLLER.create_dir(req_path)
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
        FS_CONTROLLER.rename_dir(req_path, new_name)
        return {'result': 'rename success'}
