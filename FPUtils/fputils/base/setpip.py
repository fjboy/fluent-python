from six.moves import configparser
from six.moves import urllib_parse

from fplib.common import cliparser
from fplib.common import log
from fplib import system
from fplib import fs

LOG = log.getLogger(__name__)


SECTION_GLOBAL = 'global'
OPTION_INDEX_URL = 'index-url'
SECTION_INSTALL = 'install'
OPTION_TRUST_HOST = 'trusted-host'
KNOWN_INDEX_URL = {
    'aliyun': 'http://mirrors.aliyun.com/pypi/simple',
    'douban': 'http://pypi.douban.com/simple/',
    'ustc': 'https://pypi.mirrors.ustc.edu.cn/simple/',
    'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',
}


def set_option(parser, section, option, value):
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, option, value)


class SetPip(cliparser.CliBase):
    NAME = 'set-pip'
    ARGUMENTS = [
        cliparser.Argument('-f', '--force', action='store_true',
                           help='Set config force.'),
        cliparser.Argument('index_url',
                           help='The index-url of pip, http url or one of '
                           '{}'.format(list(KNOWN_INDEX_URL.keys()))),
    ]

    def __call__(self, args):
        pip_conf = system.get_pip_path()
        fs.make_file(pip_conf)
        parser = configparser.ConfigParser()
        if not parser.has_section(SECTION_GLOBAL):
            parser.add_section(SECTION_GLOBAL)
        if args.index_url in KNOWN_INDEX_URL:
            index_url = KNOWN_INDEX_URL.get(args.index_url)
        else:
            index_url = args.index_url
        url = urllib_parse.urlsplit(index_url)
        if not args.force and(not url.scheme or not url.netloc):
            LOG.warn('%s is not a valid url, please check or use -f '
                     'to set force', index_url)
            return
        set_option(parser, SECTION_GLOBAL, OPTION_INDEX_URL, index_url)
        set_option(parser, SECTION_INSTALL, OPTION_TRUST_HOST, url.netloc)
        with open(pip_conf, 'w') as f:
            parser.write(f)
        LOG.info('update success')
