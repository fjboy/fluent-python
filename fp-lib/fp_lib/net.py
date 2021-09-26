from collections import namedtuple
from concurrent import futures
import re
import socket

from fp_lib import executor
from fp_lib import system

ScanResult = namedtuple('ScanResult', 'host port connectable')


def port_scan(host, port_start=0, port_end=65535, threads=1, callback=None):
    """scan host ports between [port_start, port_end]

    >>> port_scan('localhost',
    ...           port_start=8001,
    ...           port_end=8002,
    ...           threads=3,
    ...           callback=lambda future : print(future.done()))
    True
    True
    """
    def _connect(port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.connect((host, port))
            return ScanResult(host, port, True)
        except Exception:
            return ScanResult(host, port, False)
        finally:
            server.close()

    with futures.ThreadPoolExecutor(threads) as executor:
        for port in range(port_start, port_end + 1):
            if callback:
                executor.submit(_connect, port).add_done_callback(callback)
            else:
                executor.submit(_connect, port)


def ping(host):
    if system.OS.is_linux():
        result = executor.LinuxExecutor.execute(['ping', '-w', '3', host])
    else:
        result = executor.LinuxExecutor.execute(['ping', '-n', '3', host])
    return result.status == 0


def get_internal_ip():
    """Get the internal network IP address
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]


def get_ip_addresses(v4=True, v6=False):
    addr_types = [socket.AddressFamily.AF_INET] if v4 else []
    if v6:
        addr_types.append(socket.AddressFamily.AF_INET6)
    address_list = []
    for addr in socket.getaddrinfo(socket.gethostname(), None):
        if addr[0] in addr_types:
            address_list.append(addr[4][0])
    return address_list


def split_host_port(address, default_host=None, default_port=None):
    """Split address to host port
    The format of address like: 
        host1, host1:8888, 1.1.1.1, 1.1.1.1:8888, :8888

    >>> split_host_port('host1:8888')
    ('host1', '8888')
    >>> split_host_port('host1')
    ('host1', None)
    >>> split_host_port(':8888')
    (None, '8888')
    """
    if not address:
        return default_host, default_port
    host, port = re.match(r'([^:]+)*:*(\d+)*', address).groups()
    return host or default_host, default_port if port is None else int(port)
