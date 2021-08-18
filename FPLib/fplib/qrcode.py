import io

import pyzbar
from PIL import Image

try:
    import qrcode
except ImportError:
    pass


class QRCodeExtend(qrcode.QRCode):
    """
    >>> code = QRCodeExtend()
    >>> code.add_data('http://www.baidu.com')
    >>> lines = code.parse_string_lines()
    """
    char_map = {
        True: {True: '█', False: '▀'},
        False: {True: '▄', False: ' '}
    }

    def parse_string_lines(self):
        """parse qrcode to string lines
        """
        matrix = self.get_matrix()
        rows = len(matrix)
        columns = len(matrix[0])
        if rows / 2 != 0:
            matrix.append([False] * columns)

        def get_char(x, y):
            x_next = x + 1
            return self.char_map.get(matrix[x][y]).get(matrix[x_next][y])
        lines = []
        for line in range(0, rows, 2):
            lines.append(''.join([get_char(line, i) for i in range(columns)]))
        return lines

    def parse_image_buffer(self):
        """parse qrcode to BytesIO buffer
        """
        buffer = io.BytesIO()
        self.make_image().save(buffer)
        return buffer

    def save(self, output):
        img = self.make_image()
        img.save(output)

    @classmethod
    def dump(cls, filename):
        img = Image.open(filename)
        return [
            txt.data.decode("utf-8") for txt in pyzbar.decode(img)
        ]
