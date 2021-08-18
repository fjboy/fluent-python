from __future__ import print_function

import json
from socket import socket
import subprocess
from gevent import pywsgi

from fplib.system import OS
from fplib import net
from fplib.common import log

LOG = log.getLogger(__name__)


DEFUALT_METHOD_STATUS = {
    'GET': '200 OK',
    'POST': '201 Created',
    'PUT': '201 Updated',
    'DELETE': '204 No Content'
}


class BaseWsgiApp(object):

    def __init__(self):
        self.environ = None

    @property
    def method(self):
        return self.environ['REQUEST_METHOD']

    def get_wsgi_input_data(self):
        wsgi_input = self.environ.get('wsgi.input')
        return wsgi_input.read(
            int(self.environ.get('CONTENT_LENGTH', 0) or 0)
        )

    def __call__(self, environ, start_response):
        self.environ = environ
        if self.method not in DEFUALT_METHOD_STATUS:
            start_response('404', [])
            return ['method {} is not supported for this server'.format(self.method).encode()]
        func = getattr(self, 'do_{}'.format(self.method), None)
        resp = func(environ, start_response)
        response_headers = [('Content-Type', 'application/json')]
        start_response(resp[0], response_headers)
        return [resp[1].encode()]

    def do_GET(self, environ, start_response):
        resp = self.get()
        if isinstance(resp, str):
            return DEFUALT_METHOD_STATUS['GET'], resp
        else:
            return resp

    def do_POST(self, environ, start_response):
        req_data = self.get_wsgi_input_data()
        LOG.debug('xxxx req_data is %s', req_data)
        resp = self.post(req_data)
        if isinstance(resp, str):
            return DEFUALT_METHOD_STATUS['POST'], resp
        else:
            return resp

    def do_PUT(self, environ, start_response):
        return self.put(self)

    def do_DELETE(self, environ, start_response):
        return self.delete()

    def get(self):
        return '200 OK', 'Hello, world'

    def post(self, data):
        return '404 Not Found', 'POST is NotImplemented'

    def put(self, data):
        return '404 Not Found', 'PUT is NotImplemented'

    def delete(self):
        return '404 Not Found', 'DELETE is NotImplemented'


class CmdServer(BaseWsgiApp):
    
    def get(self):
        uname = OS.uname()
        resp_body = {'system': uname.system,
                     'version': uname.version,
                     'machine': uname.machine,
                     'processor': uname.processor,
                     'release': uname.release
        }
        return '200 OK', json.dumps(resp_body)

    def post(self, data):
        try:
            req_body = json.loads(data)
        except Exception:
            resp_body = {'error': 'request body is invalid'}
            return '400 Invalid Request', json.dumps(resp_body)
        cmd = req_body.get('cmd')
        status, output = subprocess.getstatusoutput(cmd)
        return json.dumps({'output': output, 'status': status})


def main():
    import sys

    address = sys.argv[0] if len(sys.argv) >= 2 else None
    host, port = net.split_host_port(address,
                                     default_host=net.get_internal_ip(),
                                     default_port=8888)
    log.enable_debug()
    LOG.info('start server at %s:%s', host, port)
    server = pywsgi.WSGIServer((host, port), CmdServer())
    server.serve_forever()


if __name__ == '__main__':
    main()
    print(net.get_ip_addresses())
    
