"""
Module tqdm wrapper
Prevent throwing exceptions due to import failure 
"""
try:
    from tqdm import tqdm
    is_support_tqdm = True
except ImportError:
    is_support_tqdm = False

from . import log

LOG = log.getLogger(__name__)


class ProgressNoop(object):

    def __init__(self, *args, **kwargs):
        pass

    def update(self, size):
        pass

    def close(self):
        pass

    def set_description(self, *args, **kargs):
        pass


class ProgressWithTqdm(ProgressNoop):

    def __init__(self, *args, **kwargs):
        self.pbar = tqdm(*args, **kwargs)

    def update(self, size):
        self.pbar.update(size)

    def close(self):
        self.pbar.clear()
        self.pbar.close()

    def set_description(self, *args, **kwargs):
        self.pbar.set_description(*args, **kwargs)


def factory(total):
    if is_support_tqdm:
        return ProgressWithTqdm(total=total)
    else:
        LOG.warning('Module is not installed, use Null Progress')
        return ProgressNoop(total=total)
