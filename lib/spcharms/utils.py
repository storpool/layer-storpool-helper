"""
A StorPool Juju charm helper module: miscellaneous utility functions.
"""
import os
import platform
import time

from charmhelpers.core import hookenv

from spcharms import config as spconfig
from spcharms import status as spstatus

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


def err(msg):
    """
    Log an error message and set the unit's status.
    """
    hookenv.log(msg, hookenv.ERROR)
    spstatus.set('error', msg)


def bypassed(name):
    """
    Check whether the administrator has explicitly specified that
    the installation should proceed despite some detected problems.
    """
    return name in hookenv.config().get('bypassed_checks', '').split(',')


def check_cgroups(service):
    """
    Check whether the use of cgroups is enabled in the StorPool configuration
    and, if it is, whether the cgroups defined for the specified service are
    set up on this node.
    """
    rdebug('Checking the cgroup config for {svc}'.format(svc=service))
    if bypassed('use_cgroups'):
        hookenv.log('The "use_cgroups" bypass is meant '
                    'FOR DEVELOPMENT ONLY!  DO NOT run a StorPool cluster in '
                    'production with it!', hookenv.WARNING)
        rdebug('- cgroups bypassed altogether')
        return True

    cfg = spconfig.get_dict()
    use_cgroups = cfg.get('SP_USE_CGROUPS', '0').lower()
    if use_cgroups not in ('1', 'y', 'yes', 't', 'true'):
        err('The SP_USE_CGROUPS setting is not enabled in '
            'the StorPool configuration (bypass: use_cgroups)')
        return False
    var = 'SP_{upper}_CGROUPS'.format(upper=service.upper())
    cgstr = cfg.get(var, None)
    if cgstr is None:
        err('No {var} in the StorPool configuration'.format(var=var))
        return False
    rdebug('About to examine the "{cg}" string for valid cgroups'
           .format(cg=cgstr))
    for cgdef in filter(lambda s: s != '-g', cgstr.strip().split()):
        rdebug('- parsing {d}'.format(d=cgdef))
        comp = cgdef.split(':')
        if len(comp) != 2:
            err('Unexpected component in {var}: {comp}'
                .format(var=var, comp=cgdef))
            return False
        path = '/sys/fs/cgroup/{tp}/{p}'.format(tp=comp[0], p=comp[1])
        rdebug('  - checking for {path}'.format(path=path))
        if not os.path.isdir(path):
            err('No {comp} group for the {svc}'
                .format(comp=cgdef, svc=service))
            return False

    rdebug('- the cgroups for {svc} are set up'.format(svc=service))
    return True
