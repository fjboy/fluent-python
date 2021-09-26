from fp_lib import qrcode
from fp_lib.common import cliparser
from fp_lib.common import log

LOG = log.getLogger(__name__)

DEFAULT_BORDER = 0


class QrcodeParse(cliparser.CliBase):
    NAME = 'qrcode-parse'
    ARGUMENTS = [
        cliparser.Argument('string', help='the string to create qrcode'),
        cliparser.Argument('-b', '--border', type=int, default=DEFAULT_BORDER,
                           help='the border of qrcode, deafult is {}'.format(
                               DEFAULT_BORDER)),
        cliparser.Argument('-o', '--output', default=None,
                           help='the file name to save image'),
    ]

    def __call__(self, args):
        border = args.border
        qr = qrcode.QRCodeExtend(border=border)
        qr.add_data(args.string)
        if args.output:
            qr.save(args.output)
        else:
            for line in qr.parse_string_lines():
                print(line)


class QrcodeDump(cliparser.CliBase):
    NAME = 'qrcode-dump'
    ARGUMENTS = [
        cliparser.Argument('filename', help='the image file of qrcode'),
    ]

    def __call__(self, args):
        text_lines = qrcode.QRCodeExtend.dump(args.filename)
        for line in text_lines:
            print(line)


def list_sub_commands():
    return [QrcodeParse, QrcodeDump]
