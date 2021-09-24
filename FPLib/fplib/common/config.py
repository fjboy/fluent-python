from six.moves import configparser


class Option(object):

    def __init__(self, name, default=None):
        self.name = name
        self._default = self.parse_value(default)
        self._value = None

    def parse_value(self, value):
        return value

    def set_value(self, value):
        self._value = self.parse_value(value)

    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        return self._default if self._value is None else self._value


class IntOption(Option):

    def parse_value(self, value):
        return int(value)


class BooleanOption(Option):

    def parse_value(self, value):
        return value.upper() == 'TRUE'


class ListOption(Option):

    def parse_value(self, value):
        """ list values
        e.g.
        list_option = value1
                      value2
        """
        if isinstance(value, list):
            return value
        else:
            return value.split()


class MapOption(Option):

    def parse_value(self, value):
        """ map values
        e.g.
        list_option = key1:value1
                      key2:value2
        """
        tmp_value = {}
        if isinstance(value, dict):
            tmp_value = value
        else:
            for item in value.split():
                option, value = item.split(':')
                tmp_value[option] = value
        return tmp_value

class OptGroup(object):

    def __init__(self, name):
        super(OptGroup, self).__init__()
        self.name = name
        self._options = {}

    def add_opt(self, opt):
        self._options[opt.name] = opt

    def __getattr__(self, name):
        if name in self._options:
            return self._options[name].value
        else:
            raise Exception('No such option: {}'.format(name))

    def options(self):
        return self._options.keys()

    def set_option_value(self, opt_name, value):
        self._options[opt_name].set_value(value)

    def get_options(self):
        return self._options.values()


class ConfigOpts(object):
    """Simple class for Config options
    Usage:
        1. Create Options
        2. Create global CONF
        3. Register options to CONF

    Example:
    >>> CONF = ConfigOpts()
    >>> server_opts = [Option('foo', default='foo')]
    >>> CONF.register_opts([Option('foo', default='foo1')])
    >>> CONF.register_opts([Option('foo', default='foo2')], group='bar')
    >>> CONF.bar.foo
    'foo2'
    >>> CONF.foo
    'foo1'
    >>> CONF.DEFAULT.foo
    'foo1'
    """

    def __init__(self):
        super(ConfigOpts, self).__init__()
        self._groups = {
            configparser.DEFAULTSECT: OptGroup(configparser.DEFAULTSECT)}
        self._conf_files = []

    def __getattr__(self, name):
        if name in self._groups:
            return self._groups[name]
        else:
            return getattr(self._groups[configparser.DEFAULTSECT], name)

    def register_opts(self, options, group=configparser.DEFAULTSECT):
        for option in options:
            self.register_opt(option, group=group)

    def register_opt(self, option, group=configparser.DEFAULTSECT):
        if group not in self._groups:
            self._groups[group] = OptGroup(group)
        self._groups[group].add_opt(option)

    def groups(self):
        return self._groups.keys()

    def get_groups(self):
        return self._groups.values()

    def load(self, conf_file):
        parser = configparser.RawConfigParser()
        parser.read(conf_file)
        for group_name in self.groups():
            if not parser.has_section(group_name):
                continue
            opt_group = getattr(self, group_name)
            for opt_name in getattr(self, group_name).options():
                if not parser.has_option(group_name, opt_name):
                    continue
                opt_group.set_option_value(
                    opt_name, parser.get(group_name, opt_name))
        self._conf_files.append(conf_file)

    def conf_files(self):
        return self._conf_files
