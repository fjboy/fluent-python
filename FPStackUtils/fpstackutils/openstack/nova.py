from __future__ import print_function
from concurrent import futures
from re import S
import eventlet
import threading
import contextlib

from fplib.common import log
from fpstackutils.openstack import client

LOG = log.getLogger(__name__)


class ServerCleanUp(object):
    
    def __init__(self):
        self.openstack = client.OpenstackClient.create_instance()
        self.percent = 0
        self.progress_format = 'progress: {:.2f}% {}'

    def cleanup(self, name=None, workers=None):
        workers = workers or 1
        servers = self._list(name=name)
        self.percent = 0

        while len(servers) > 0:
            LOG.info('delete %s vms ...' % len(servers))
            with self.start_progress(len(servers)) as progress:
                deleted = 0
                with futures.ThreadPoolExecutor(
                    max_workers=workers) as executor:
                    for result in executor.map(self._delete, servers):
                        deleted += 1
                        progress['computed'] = deleted

            servers = self._list(name=name)

    def _delete(self, server):
        return self.openstack.nova.servers.delete(server.id)

    def _list(self, name=None):
        LOG.info('get servers')
        servers = []
        for s in self.openstack.nova.servers.list():
            if name and (name not in s.name):
                LOG.info('skip to delete server: %s(%s)', s.name, s.id)
                continue
            if getattr(S, 'OS-EXT-STS:task_state') == 'deleting':
                continue
            servers.append(s)
        return servers

    @contextlib.contextmanager
    def start_progress(self, total, interva=1):
        self.percent = 0
        progress = {'computed': 0, 'total': total}
        t = threading.Thread(target=self.print_progress, args=(progress,))
        t.setDaemon(True)
        t.start()
        yield progress
        t.join()

    def print_progress(self, progress, interval=1):
        
        while True:
            percent = progress['completed'] * 100 / len(progress['total'])
            if percent >= 100:
                break
            print(self.progress_format.format(percent, '▋' * percent),
                  end='\r')
            eventlet.sleep(interval)
        print()
