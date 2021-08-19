import os
import json
import flask

from six.moves import urllib_parse

from flask import views
from flask import current_app

from fplib.common import log
from fplib import qrcode
from fplib import fs

LOG = log.getLogger(__name__)
FS_CONTROLLER = None

SERVER_NAME = 'FluentHttpFS'
VERSION = 1.0

DEFAULT_CONTEXT = {
    'name': SERVER_NAME,
    'version': VERSION
}


def get_json_response(data, status=200):
    return flask.Response(json.dumps(data), status=status)


class HomeView(views.MethodView):

    def get(self):
        return flask.redirect('/index.html')


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html', **DEFAULT_CONTEXT)


class QrcodeView(views.MethodView):

    def get(self):
        qr = qrcode.QRCodeExtend(border=1)
        file_name = flask.request.args.get('file')
        file_path = flask.request.args.getlist('path_list') or []
        if file_name and file_path is not None:
            content = urllib_parse.urlunparse([
                'http', current_app.config['SERVER_NAME'],
                'download/{0}'.format(file_name), None,
                urllib_parse.urlencode({'path_list': file_path}, doseq=True),
                None])
        else:
            content = urllib_parse.urlunparse([
                'http', current_app.config['SERVER_NAME'], '', None,
                None, None])
        LOG.debug('qrcode file_path is %s', file_path)
        LOG.debug('qrcode content is %s', content)
        qr.add_data(content)
        buffer = qr.parse_image_buffer()
        return buffer.getvalue()


class DownloadView(views.MethodView):

    def get(self, file_name):
        req_path = flask.request.args.getlist('path_list')
        req_path.append(file_name)
        LOG.debug('get file %s', req_path)
        if not FS_CONTROLLER.path_exists(req_path):
            return get_json_response({'error': 'path required is not exists'},
                                     status=404)
        if FS_CONTROLLER.is_file(req_path):
            return self.download_file(req_path)
        else:
            return self.download_dir(req_path)

    def download_file(self, file_path):
        abs_path = FS_CONTROLLER.get_abs_path(file_path)
        LOG.debug('download file %s', abs_path)
        try:
            directory = os.path.dirname(abs_path)
        except Exception as e:
            LOG.exception(e)
            return get_json_response({'error': 'file not found'}, status=404)

        return flask.send_from_directory(
            directory, os.path.basename(abs_path), as_attachment=False)

    def download_dir(self, dir_path):
        abs_path = FS_CONTROLLER.get_abs_path(dir_path)
        zip_name = fs.zip_path(abs_path)
        if not os.path.exists(zip_name):
            return get_json_response({'error': 'zip failed'}, status=400)

        LOG.debug('download dir %s', dir_path)
        return flask.send_from_directory('./', zip_name, as_attachment=False)


class ActionView(views.MethodView):

    ACTION_MAP = {
        'list_dir': 'list_dir',
        'create_dir': 'create_dir',
        'delete_dir': 'delete_dir',
        'get_qrcode': 'get_qrcode',
        'rename_dir': 'rename_dir',
        'get_file': 'get_file',
        'upload_file': 'upload_file',
        'search': 'search',
        'download': 'download',
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

    def list_dir(self, params):
        # self._check_params(params)
        req_path = params.get('path')
        if not req_path:
            req_path = params.get('path_items')
        usage = FS_CONTROLLER.disk_usage()
        children = FS_CONTROLLER.get_dirs(req_path,
                                          all=params.get('all', False))
        for child in children:
            child['qrcode'] = self._get_file_qrcode_link(child, req_path)
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

    def _get_file_qrcode_link(self, path_dict, path_list):
        if path_dict['type'] == 'folder':
            return ''
        params = {'file': path_dict['name'], 'path_list': path_list}
        return '/qrcode?{0}'.format(urllib_parse.urlencode(params,
                                                           doseq=True))

    def create_dir(self, params):
        req_path = params.get('path_items')
        if FS_CONTROLLER.path_exists(req_path):
            raise ValueError('path is already exists: %s' % req_path)
        FS_CONTROLLER.create_dir(req_path)
        return {'result': 'create success'}

    def delete_dir(self, params):
        FS_CONTROLLER.delete_dir(params.get('path_items'),
                                 force=params.get('force'))
        return {'result': 'delete success'}

    def rename_dir(self, params):
        '''
        params: {'path': 'xxx', 'file': 'yy', 'new_name': 'yy1'}
        '''
        self._check_params(params)
        if not params.get('new_name'):
            return get_json_response({'error': 'new name is none'}, status=400)
        FS_CONTROLLER.rename_dir(
            os.path.join(params.get('path'), params.get('file') or ''),
            params.get('new_name'),
        )
        return {'result': 'rename success'}

    def _check_params(self, params):
        req_path = params.get('path') or params.get('path_list')

        if not req_path:
            raise ValueError('path is None')
        if req_path and not FS_CONTROLLER.path_exists(req_path):
            raise ValueError('path is not exists: %s' % req_path)

    def get_file(self, params):
        '''
        params: {'path_list': [] , 'file': 'yy'}
        '''
        if not params.get('file'):
            return get_json_response({'error': 'file name is none'},
                                     status=400)
        file_path = params.get('path_list')[:]
        file_path.append(params.get('file'))
        content = FS_CONTROLLER.get_file_content(file_path)
        return {'file': {
            'name': params.get('file'),
            'content': content}
        }

    def search(self, params):
        """
        params: {'partern': '*.py'}
        """
        matched_pathes = []
        if params.get('partern'):
            for file_item in FS_CONTROLLER.search(params.get('partern')):
                LOG.debug('file_item %s', file_item)
                file_item['qrcode'] = self._get_file_qrcode_link(
                    file_item, file_item['pardir'])
                matched_pathes.append(file_item)
        return {'dirs': matched_pathes}

    def download(self, params):
        """
        params: {'path_list': [] , 'file': 'yy'}
        """


class FaviconView(views.MethodView):

    def get(self):
        return flask.send_from_directory(current_app.static_folder,
                                         'httpfs.png')
