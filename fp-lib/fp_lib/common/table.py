from __future__ import print_function
from fp_lib.common import colorstr

class SimpleTable(object):
    """
    
    >>> st = SimpleTable()
    >>> st.set_header(['Head1', 'Head2'])
    >>> st.add_row(['111111111111', '2'])
    >>> st.add_row(['xxxxxxxxxxxxxxxxx', 'bb'])
    >>> st.dumps()
    Head1            |Head2
    -----------------+-----
    111111111111     |2
    xxxxxxxxxxxxxxxxx|bb
    """
    def __init__(self):
        self.header_cols = []
        self.rows = []
        self.col_max_len = {}

    def _update_col_max_len(self, cols):
        for i, col in enumerate(cols):
            self.col_max_len[i] = max(len(col), self.col_max_len.get(i) or 0)

    def set_header(self, cols):
        self._update_col_max_len(cols)
        self.header_cols = cols

    def add_row(self, cols):
        self._update_col_max_len(cols)
        self.rows.append(cols)

    def dumps(self):
        output_lines = []
        col_str_list = []
        for i, col in enumerate(self.header_cols):
            col_str = str(colorstr.BlueStr(
                '{{:{}}}'.format(self.col_max_len.get(i)).format(col)))
            col_str_list.append(col_str)
        output_lines.append('|'.join(col_str_list))
        output_lines.append(
            '+'.join([
                '-' * self.col_max_len[i] for i in range(len(self.col_max_len))
            ]))
        for row in self.rows:
            col_str_list = []
            for i, col in enumerate(row):
                col_str = '{{:{}}}'.format(self.col_max_len.get(i)).format(col)
                col_str_list.append(col_str)
            output_lines.append('|'.join(col_str_list))

        return '\n'.join(output_lines)
