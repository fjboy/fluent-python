import memcache


def get_memcached_client(servers, debug=False):
    """
        mc.set("name", "python")
        ret = mc.get('name')
        print(ret)
    """
    if isinstance(servers, str):
        servers = servers.split(',')
    return memcache.Client(servers, debug=debug)
