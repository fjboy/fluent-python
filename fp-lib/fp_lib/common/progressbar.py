"""
Module tqdm wrapper
Prevent throwing exceptions due to import failure 
"""
from __future__ import print_function
import time
import threading
try:
    from tqdm import tqdm
    is_support_tqdm = True
except ImportError:
    is_support_tqdm = False

from fp_lib import date

from . import log

LOG = log.getLogger(__name__)


class ProgressNoop(object):

    def __init__(self, total, **kwargs):
        self.total = total

    def update(self, size):
        pass

    def close(self):
        pass

    def set_description(self, *args, **kargs):
        pass


class ProgressWithPrint(ProgressNoop):
    progress_format = '{}   {:3}% [{:100}]\r'

    def __init__(self, total, **kwargs):
        super(ProgressWithPrint, self).__init__(total)
        self.progress = {'completed': 0, 'total': self.total}
        self.last_time = time.time()
        self.lock = threading.Lock()

    def update(self, size):
        self.lock.acquire()
        self.progress['completed'] += size
        if time.time() - self.last_time >= 2:
            self._print_progress()
            self.last_time = time.time()
        self.lock.release()

    def close(self):
        self._print_progress()

    def _print_progress(self):
        percent = self.progress['completed'] * 100 / self.progress['total']
        print(self.progress_format.format(
            date.parse_timestamp2str(time.time()), percent, '#' * percent))


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
        LOG.warning('tqdm is not installed, use ProgressWithPrint')
        return ProgressWithPrint(total=total)
