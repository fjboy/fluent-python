
class UnknownException(Exception):
    msg = 'unkown exception'

    def __init__(self, **kwargs):
        super(UnknownException, self).__init__(self.msg.format(**kwargs))


class UnknownComponent(UnknownException):
    msg = 'unknown component {component}'


class ComponentStarted(UnknownException):
    msg = '{component} is started'

