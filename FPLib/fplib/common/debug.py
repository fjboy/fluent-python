import os
import time
import logging

from fplib.common import log

FORMAT = '%(asctime)s %(levelname)s %(message)s'


def get_file_logger(file_name):
    name = os.path.basename(file_name).split('.log')[0]
    logger = log.getLogger(name, file_name=file_name, format=FORMAT)
    logger.setLevel(logging.DEBUG)
    return logger


def log_func_spend(logger=None):
    if not logger:
        logger = get_file_logger('./debugger.log')
    elif isinstance(logger, str):
        logger = get_file_logger(logger)

    def wrapper(func):
        func_name = '{}.{}'.format(func.__module__, func.__name__)

        def wrapper_func(*args, **kwargs):
            start_time = time.time()
            logger.debug('begin function: %s', func_name)
            result = func(*args, **kwargs)
            logger.debug('end function: %s, spend %.6f seconds',
                         func_name, time.time() - start_time)
            return result

        return wrapper_func
    return wrapper
