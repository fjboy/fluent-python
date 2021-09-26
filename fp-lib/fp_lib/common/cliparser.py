import sys
import argparse
import logging

from fp_lib.common import log

LOG = log.getLogger(__name__)


class Argument(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class CliBase(object):
    """Add class property NAME to set subcommaon name
    """
    BASE_ARGUMENTS = [
        Argument('-d', '--debug', action='store_true',
                 help='show debug messages'),
        Argument('-v', '--verbose', action='store_true',
                 help='show verbose messages'),
    ]
    ARGUMENTS = []

    def __call__(self, args):
        raise NotImplementedError()

    @classmethod
    def arguments(cls):
        return cls.BASE_ARGUMENTS + cls.ARGUMENTS


class SubCliParser(object):

    def __init__(self, title):
        self.parser = argparse.ArgumentParser()
        self.sub_parser = self.parser.add_subparsers(title=title)
        self._args = None

    def parse_args(self):
        self._args = self.parser.parse_args()
        if not hasattr(self._args, 'cli'):
            self.print_usage()
            sys.exit(1)
        if hasattr(self._args, 'debug') and self._args.debug:
            log.set_default(level=logging.DEBUG)
        LOG.debug('args is %s', self._args)
        return self._args

    def call(self):
        if not self._args:
            self.parse_args()
        return self._args.cli()(self._args)

    def register_clis(self, *args):
        for arg in args:
            self.register_cli(arg)

    def register_cli(self, cls):
        """params cls: CliBase type"""
        if not issubclass(cls, CliBase):
            raise ValueError('unknown type {}'.format(type(cls)))
        name = cls.NAME if hasattr(cls, 'NAME') else cls.__name__
        cli_parser = self.sub_parser.add_parser(name)
        for argument in cls.arguments():
            cli_parser.add_argument(*argument.args, **argument.kwargs)
        cli_parser.set_defaults(cli=cls)
        return cli_parser

    def print_usage(self):
        self.parser.print_usage()

    def print_help(self):
        self.parser.print_help()


def get_sub_cli_parser(title):
    return SubCliParser(title)


def register_cli(sub_cli_parser):

    def wrapper(cls):
        cli_parser = sub_cli_parser.sub_parser.add_parser(cls.NAME)
        for argument in cls.ARGUMENTS:
            cli_parser.add_argument(*argument.args, **argument.kwargs)
        cli_parser.set_defaults(cli=cls)
        return cls

    return wrapper
