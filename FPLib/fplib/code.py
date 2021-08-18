import hashlib
import io
import os
import random

from fplib.common import progressbar

LOWER = 'abcdefghijklmnopqrstuvwxyz'
UPPER = 'abcdefghijklmnopqrstuvwxyz'.upper()
NUMBER = '0123456789'
SPECIAL = '!@#$%^&*,.;:'
CHAR_MAP = {'lower': LOWER,
            'upper': UPPER,
            'number': NUMBER,
            'special': SPECIAL}

base_prefix = {'0b': 2, '0x': 16, '0o': 8}
base_func = {
    2: bin,
    8: oct,
    10: str,
    16: hex
}


def md5sum_file(file_path, read_bytes=None, sha1=False, progress=False):
    """Calculate the md5 and sha1 values of the file
    Return: md5sum, sha1
    """
    read_bytes = read_bytes or io.DEFAULT_BUFFER_SIZE
    sha1 = hashlib.sha1()
    md5sum = hashlib.md5()

    def read_from_fo(fo):
        data = fo.read(read_bytes)
        while data:
            yield data
            data = fo.read(read_bytes)

    with open(file_path, 'rb') as f:
        file_size = os.fstat(f.fileno()).st_size
        pbar = progressbar.factory(file_size) if progress \
            else progressbar.ProgressWithNull(file_size)

        for data in read_from_fo(f):
            md5sum.update(data)
            if sha1:
                sha1.update(data)
            pbar.update(len(data))
        pbar.close()
    return (md5sum.hexdigest(), (sha1 and sha1.hexdigest()) or None)


def convert_base(src_number, target_base, src_base=None):
    """Convert the number to the specified base

    >>> convert_base(10, 2)
    '1010'
    >>> convert_base('10', 2)
    '1010'
    >>> convert_base('10', 10, src_base=8)
    '8'
    >>> convert_base('10', 10, src_base=10)
    '10'
    >>> convert_base('10', 16, src_base=10)
    'a'
    >>> convert_base(11, 16)
    'b'
    """
    if target_base not in base_func:
        raise ValueError('Only support base: %s' % base_func.keys())
    if src_base is None:
        if isinstance(src_number, int):
            src_base = 10
        else:
            src_base = base_prefix.get(src_number[:2], 10)
    if src_base == target_base:
        return src_number

    # NOTE int() fist arg must be string
    base10 = int(str(src_number), src_base)
    target_num = base_func.get(target_base)(base10)
    if target_num[:2] in ['0b', '0x', '0o']:
        return target_num[2:]
    else:
        return target_num


def random_password(lower=4, upper=None, number=None, special=None):
    """Generate random password

    Args:
        lower (int, optional): the num of lower char. Defaults to 4.
        upper (int, optional): the num of upper char. Defaults to 4.
        number (int, optional): the num of number char. Defaults to 4.
        special (int, optional): the num of special char. Defaults to 4.

    Returns:
        str: the password include specified types

    >>> len(random_password()) == 4
    True
    >>> len(random_password(lower=50)) == 50
    True
    >>> len(random_password(special=20)) == 24
    True
    """
    kwargs = locals()
    password = []
    for char_type, char_num in kwargs.items():
        if not char_num:
            continue
        max_num = len(CHAR_MAP[char_type])
        tmp_num = char_num
        while tmp_num > 0:
            password += random.sample(CHAR_MAP[char_type],
                                      min(tmp_num, max_num))
            tmp_num -= max_num

    random.shuffle(password)
    return ''.join(password)
