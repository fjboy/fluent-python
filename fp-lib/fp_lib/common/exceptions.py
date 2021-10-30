
class BaseException(Exception):
    _msg = 'something wrong, reason is: {reason}'

    def __init__(self, *args, **kwargs):
        super(BaseException, self).__init__(self._msg.format(*args, **kwargs))


class ValueIsNone(BaseException):
    _msg = 'the value for {} is none'


class EnvIsNone(BaseException):
    _msg = 'the value of {} in env is none'

