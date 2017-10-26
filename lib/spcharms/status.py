"""
A StorPool Juju charm helper module: persistent unit status message.
"""

from charmhelpers.core import hookenv, unitdata


def get():
    """
    Get the persistent status as a (status, message) tuple or None.
    """
    st = unitdata.kv().get('storpool-utils.persistent-status', default=None)
    if st is None:
        return None
    return st.split(':', 1)


def set(status, msg):
    """
    Set a persistent status and message.
    """
    hookenv.status_set(status, msg)
    unitdata.kv().set('storpool-utils.persistent-status', status + ':' + msg)


def reset():
    """
    Remove a persistent status.
    """
    unitdata.kv().unset('storpool-utils.persistent-status')


def npset(status, message):
    """
    Set the unit's status if no persistent status has been set.
    """
    if not get():
        hookenv.status_set(status, message)
