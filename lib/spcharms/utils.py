"""
A StorPool Juju charm helper module: miscellaneous utility functions.
"""
import platform
import time

from charmhelpers.core import hookenv

rdebug_node = platform.node()


def rdebug(s, prefix='storpool'):
    """
    Log a diagnostic message through the charms model logger and also,
    if explicitly requested in the charm configuration, to a local file.
    """
    global rdebug_node
    data = '[[{hostname}:{prefix}]] {s}'.format(hostname=rdebug_node,
                                                prefix=prefix,
                                                s=s)
    hookenv.log(data, hookenv.DEBUG)

    config = hookenv.config()
    def_fname = '/dev/null'
    fname = def_fname if config is None \
        else config.get('storpool_charm_log_file', def_fname)
    if fname != def_fname:
        with open(fname, 'a') as f:
            data_ts = '{tm} {data}'.format(tm=time.ctime(), data=data)
            print(data_ts, file=f)


def check_in_lxc():
    """
    Check whether we are currently running within an LXC/LXD container.
    """
    try:
        with open('/proc/1/environ', mode='r') as f:
            contents = f.read()
            return bool(list(filter(lambda s: s == 'container=lxc',
                                    contents.split('\x00'))))
    except Exception:
        return False
