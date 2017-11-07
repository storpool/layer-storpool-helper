"""
A StorPool Juju charm helper module for accessing the StorPool configuration.
"""
import subprocess

from charmhelpers.core import unitdata

cached_config = None

CONFIG_KEY = 'storpool-config.our-id'


def get_cached_dict():
    """
    Get the StorPool configuration, cache it the first time.
    """
    global cached_config
    if cached_config is not None:
        return cached_config

    res = {}
    lines_b = subprocess.check_output(['/usr/sbin/storpool_confshow'])
    for line in lines_b.decode().split('\n'):
        fields = line.split('=', 1)
        if len(fields) < 2:
            continue
        res[fields[0]] = fields[1]
    cached_config = res
    return cached_config


def get_dict():
    """
    Get the StorPool configuration.
    """
    return get_cached_dict()


def drop_cache():
    """
    Drop the StorPool configuration cache.
    """
    global cached_config
    cached_config = None


def get_our_id():
    """
    Fetch the cached SP_OURID value from the unit's database.
    """
    return unitdata.kv().get(CONFIG_KEY, None)


def set_our_id(value):
    """
    Store the SP_OURID value into the unit's database.
    """
    unitdata.kv().set(CONFIG_KEY, value)


def unset_our_id():
    """
    Store the SP_OURID value into the unit's database.
    """
    unitdata.kv().unset(CONFIG_KEY)
