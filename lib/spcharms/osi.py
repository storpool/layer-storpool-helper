"""
A StorPool Juju charm helper module for keeping track of the Cinder container.
"""
from charmhelpers.core import unitdata


def lxd_cinder_name():
    """
    Get the previously cached name of the local Cinder LXD container.
    """
    return unitdata.kv().get('storpool-openstack-integration.lxd-name',
                             default=None)
