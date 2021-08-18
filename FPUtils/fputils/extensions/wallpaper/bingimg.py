from fplib.common import log
from fplib.downloader.urllib import driver as urllib_driver
import importlib

LOG = log.getLogger(__name__)

SCHEME = 'http'
HOST = 'www.bingimg.cn'
FILE_NAME_MAX_SIZE = 50
URL_GET_IMAGES_PAGE = '{scheme}://{host}/list{page}'


DRIVERS = {
    'wget': 'fplib.downloader.wget.driver.WgetDriver',
    'urllib3': 'fplib.downloader.urllib.driver.Urllib3Driver'
}


class Downloader(object):

    def __init__(self, host=None, scheme=None, use_wget=False, workers=None,
                 timeout=None, download_dir=None, progress=False):
        self.scheme = scheme or SCHEME
        self.host = host or HOST
        self.workers = workers or 1
        self.timeout = timeout
        self.download_dir = download_dir
        self.driver_name = 'wget' if use_wget else 'urllib3'
        self.progress = progress
        self._driver = None

    @property
    def driver(self):
        if not self._driver:
            mod, _, klass = DRIVERS.get(self.driver_name).rpartition('.')
            driver_cls = getattr(importlib.import_module(mod), klass)
            self._driver = driver_cls(download_dir=self.download_dir,
                                      timeout=self.timeout,
                                      workers=self.workers,
                                      progress=self.progress,
                                      headers=self.default_headers)
        return self._driver

    @property
    def default_headers(self):
        return {
            'Connection': 'keep-alive',
            'Host': self.host,
            'Referer': '{0}://{1}/'.format(self.scheme, self.host),
        }

    def download(self, page, resolution=None):
        """Download images found in page

        page : int
            the page number of bingimg web pages
        resolution : string, optional
            the resolution of image to download, by default None
        threads : int, optional
            download threads, if None, save, by default None
        progress : bool, optional
            show progress, by default False
        """
        img_links = self.find_image_links(page, resolution=resolution)
        LOG.info('found %s links in page %s.', len(img_links), page)
        self.driver.download_urls(img_links)

    def find_image_links(self, page, resolution=None):
        link_regex = r'.*\.(jpg|png)$' if not resolution else \
                     r'.*{}.*\.(jpg|png)$'.format(resolution)
        return urllib_driver.find_links(self.get_page_url(page),
                                        link_regex=link_regex,
                                        headers=self.default_headers)

    def get_page_url(self, page):
        return URL_GET_IMAGES_PAGE.format(scheme=self.scheme,
                                          host=self.host, page=page)
