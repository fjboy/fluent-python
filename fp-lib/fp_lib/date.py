import time
import pytz
from datetime import datetime
from datetime import timedelta

FORMAT_YYYY_MM_DD_HHMMSS = '%Y-%m-%d %H:%M:%S'
FORMAT_YYYY_MM_DD_HHMMSS_Z = '%Y-%m-%d %H:%M:%S %Z'


def parse_timestamp2str(timestamp, date_format=None):
    """Parse timestamp to string with DATE_FORMAT

    >>> parse_timestamp2str(0.0, date_format=FORMAT_YYYY_MM_DD_HHMMSS)
    '1970-01-01 08:00:00'
    """
    dt = datetime.fromtimestamp(timestamp)
    if not date_format:
        return dt.isoformat()
    else:
        return dt.strftime(date_format)


def parse_str2timestamp(datetime_str, date_format=None):
    """Parse timestamp to string with DATE_FORMAT
    >>> parse_str2timestamp('1970-01-01 08:00:00')
    0.0
    """
    if not date_format:
        date_format = FORMAT_YYYY_MM_DD_HHMMSS
    return time.mktime(time.strptime(datetime_str, date_format))


parse_ts2str = parse_timestamp2str
parse_str2ts = parse_str2timestamp


def now(tz=None):
    """return type: datetime
    """
    timezone = pytz.timezone(tz) if tz else None
    return datetime.now(tz=timezone)


def now_str(tz=None, date_format=None):
    date_now = now(tz=tz)
    if not date_format:
        return date_now.isoformat()
    else:
        return date_now.strftime(date_format)


def utc_now():
    """return type: datetime
    """
    return datetime.utcnow(tz='utc')


def utc_now_str(date_format=None):
    return now_str(tz='utc', date_format=date_format)


def datetime_after(start=None, **kwargs):
    return (start or datetime.now()) + timedelta(**kwargs)


def datetime_before(end=None, **kwargs):
    return (end or datetime.now()) - timedelta(**kwargs)
