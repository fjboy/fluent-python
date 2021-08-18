import locale
import pytz

_COUNTRY = locale.getdefaultlocale()[0].split('_')[-1]


def set_country(country):
    global _COUNTRY
    if country not in pytz.country_names:
        raise ValueError('country %s is not exists.' % country)
    else:
        _COUNTRY = country


def get_country():
    """use module pytz to get country"""
    global _COUNTRY
    assert _COUNTRY is not None
    return pytz.country_names.get(_COUNTRY)


def get_country_timezones(country=None):
    """Get timezones by country code

    >>> get_country_timezones(country='CN')
    ['Asia/Shanghai', 'Asia/Urumqi']
    """
    return pytz.country_timezones[country or _COUNTRY]
