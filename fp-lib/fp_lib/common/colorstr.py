WHITE = 30
RED = 31
GREEN = 32
YELLOW = 33
BLUE = 34
PURLE = 35

RED_BACKGROUPD = 41
GREEN_BACKGROUPD = 42
YELLOW_BACKGROUPD = 43
BLUE_BACKGROUPD = 44
PURLE_BACKGROUPD = 45


def make_str(style, content):
    return '\033[1;{}m{}\033[0m'.format(style, content)


class WhiteStr(object):
    style = WHITE

    def __init__(self, content):
        self.content = content

    def __str__(self):
        return make_str(self.style, self.content)


class RedStr(WhiteStr):
    style = RED


class GreenStr(WhiteStr):
    style = GREEN


class BlueStr(WhiteStr):
    style = BLUE


class PurpleStr(WhiteStr):
    style = PURLE


class YellowStr(WhiteStr):
    style = YELLOW
