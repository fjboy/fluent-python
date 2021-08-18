import logging
from logging import handlers

_DEFAULT_LEVEL = logging.INFO
_DEFAULT_FORMAT = '%(asctime)s %(levelname)s %(name)s:%(lineno)s %(message)s'
_DEFAULT_FILE = None
_DEFAULT_MAX_BYTES = 0
_DEFAULT_BACKUP_COUNT = 1

_LOGGER = set([])


def disable_debug():
    global _DEFAULT_LEVEL
    _DEFAULT_LEVEL = logging.INFO


def enable_debug():
    global _DEFAULT_LEVEL
    _DEFAULT_LEVEL = logging.DEBUG
    for name in _LOGGER:
        logger = logging.getLogger(name)
        logger.setLevel(_DEFAULT_LEVEL)


def set_default(level=None, filename=None, max_mb=None, backup_count=None):
    global _DEFAULT_LEVEL
    global _DEFAULT_FILE, _DEFAULT_MAX_BYTES, _DEFAULT_BACKUP_COUNT
    if level:
        _DEFAULT_LEVEL = level
    if filename:
        _DEFAULT_FILE = filename
    if max_mb:
        _DEFAULT_MAX_BYTES = 1024 * 1024 * max_mb
    if backup_count:
        _DEFAULT_BACKUP_COUNT = backup_count

    for name in _LOGGER:
        logger = logging.getLogger(name)
        logger.setLevel(_DEFAULT_LEVEL)
        if not logger.handlers:
            logger.addHandler(get_handler())
        else:
            logger.handlers[0] = get_handler()


def load_config(config_file):
    logging.config.fileConfig(config_file)


def get_handler(file_name=None, format=None):
    file_name = file_name or _DEFAULT_FILE
    if file_name:
        handler = handlers.RotatingFileHandler(
            file_name, mode='a',
            maxBytes=_DEFAULT_MAX_BYTES,
            backupCount=_DEFAULT_BACKUP_COUNT)
    else:
        handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(format or _DEFAULT_FORMAT))
    return handler


def getLogger(name, file_name=None, format=None):
    """
    >>> set_default(filename='test.log', level=logging.DEBUG)
    >>> LOG = getLogger(__name__)
    >>> LOG.debug('debug')
    >>> LOG.info('info' * 100)
    >>> LOG.error('error')
    """
    global _LOGGER
    _LOGGER.add(name)
    logger = logging.getLogger(name)
    logger.setLevel(_DEFAULT_LEVEL)
    if not logger.handlers:
        handler = get_handler(file_name=file_name, format=format)
        logger.addHandler(handler)
    return logger
