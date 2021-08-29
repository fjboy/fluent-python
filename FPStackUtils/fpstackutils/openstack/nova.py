from __future__ import print_function
from concurrent import futures
import eventlet
import threading

from fplib.common import log
from fpstackutils.openstack import client

LOG = log.getLogger(__name__)


percent = 0

def print_progress():
    while percent < 100:
        print('progress: {:.2f} % {}'.format(percent, '▋' * percent), end='\r')
        eventlet.sleep(1)
    print('progress: {:.2f} %'.format(percent))


def concurrent_delete_servers(workers=10, name=None):
    global percent
    cli = client.OpenstackClient.create_instance()

    def _delete(server):
        if name and (name in server.name):
            LOG.info('skip to delete server: %s(%s)', server.name, server.id)
            return
        LOG.debug('delete server %s', server)
        cli.nova.servers.delete(server.id)

    LOG.info('get servers')
    servers = []
    for server in cli.nova.servers.list():
        if getattr(server, 'OS-EXT-STS:task_state') == 'deleting':
            continue
        servers.append(server)

    while len(servers) > 0:
        LOG.info('delete %s vms ...' % len(servers))
        t = threading.Thread(target=print_progress)
        t.setDaemon(True)
        t.start()

        percent = 0
        deleted = 0
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            for r in executor.map(_delete, servers):
                deleted += 1
                percent = deleted * 100 / len(servers)

        LOG.info('get servers')
        servers = cli.nova.servers.list()
        t.join()
