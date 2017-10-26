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

    The special `status` value of "error" is used to indicate a persistent
    error (see the `reset_unless_error()` function below); the unit status
    itself is set to "maintenance" instead.
    """
    hookenv.status_set(status if status != 'error' else 'maintenance', msg)
    unitdata.kv().set('storpool-utils.persistent-status', status + ':' + msg)


def reset():
    """
    Remove a persistent status.
    """
    unitdata.kv().unset('storpool-utils.persistent-status')


def reset_unless_error():
    """
    Remove a persistent status unless it signifies an error.
    """
    st = get()
    if st is None or st[0] != 'error':
        reset()
        hookenv.status_set('maintenance', '')


def npset(status, message):
    """
    Set the unit's status if no persistent status has been set.
    """
    if not get():
        hookenv.status_set(status, message)
