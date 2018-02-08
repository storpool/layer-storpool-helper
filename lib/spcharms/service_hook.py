"""
A StorPool Juju charms helper module that keeps track of peer units of
the same charm so that the state may be reported to other charms.
"""
import json

from charmhelpers.core import hookenv, unitdata

from spcharms import config as spconfig
from spcharms import kvdata


def init_state():
    """
    Initialize the local state as an empty dictionary.
    """
    return {}


def get_state(db=None):
    """
    Fetch the cached state or, if none, initialize it anew.
    """
    if db is None:
        db = unitdata.kv()
    state = db.get(kvdata.KEY_PRESENCE, default=None)
    if state is None:
        state = init_state()
        changed = True
    else:
        changed = False
    return (state, changed)


def set_state(db, state):
    """
    Cache the current presence state in the unit's persistent storage.
    """
    db.set(kvdata.KEY_PRESENCE, state)


def update_state(db, state, changed, key, name, value):
    """
    Update the state of a single node in the database and, if it has indeed
    been changed, store it into the persistent storage.
    """
    if key not in state:
        state[key] = {}
        changed = True
    if state[key].get(name, '') != value:
        state[key][name] = value
        changed = True

    if changed:
        set_state(db, state)
    return changed


def add_present_node(service, name, value, rdebug=lambda s: s):
    """
    Update a peer's state.
    """
    db = unitdata.kv()
    (state, changed) = get_state(db)
    return update_state(db, state, changed, service, name, value)


def get_present_nodes(service):
    """
    Fetch the current state of the charm's units.
    """
    (state, _) = get_state()
    return state.get(service, {})


def handle(data, rdebug=lambda s: s):
    """
    Handle a state change of the internal hook; update our state if needed.
    """
    rdebug('service_hook.handle {ks}'.format(ks=sorted(data.keys())))
    db = unitdata.kv()
    (state, changed) = get_state(db)
    rdebug('- current state: {state}'.format(state=state))
    rdebug('- changed even at the start: {changed}'.format(changed=changed))

    # TODO: handle detaching in an entirely different way
    for (svc, sdata) in data.items():
        for (name, value) in sdata.items():
            if update_state(db, state, changed, svc, name, value):
                rdebug('- changed: service "{svc}" name "{name}" '
                       'value "{value}"'
                       .format(svc=svc, name=name, value=value))
                changed = True

    if changed:
        rdebug('- updated state: {state}'.format(state=state))
    return changed


def get_remote_presence():
    """
    Get the presence data sent down a storpool-service/presence interface.
    """
    conf = unitdata.kv().get(kvdata.KEY_REMOTE_PRESENCE)
    if conf.get('version') != '1.0':
        raise Exception('Internal error: presence data with weird version')
    presence = conf.get('presence')
    if presence is None:
        return None
    elif 'data' not in presence:
        raise Exception('Internal error: presence data with no, uhm, data')
    return presence['data']


def get_remote_config():
    """
    Get the configuration sent down a storpool-service/presence interface.
    """
    conf = unitdata.kv().get(kvdata.KEY_REMOTE_PRESENCE)
    return conf.get('config')


def import_presence(conf):
    """
    Parse the presence data sent down a storpool-service/presence interface.
    """
    if 'version' not in conf:
        raise Exception('Internal error: presence data with no version')
    elif not conf['version'].startswith('1.'):
        raise Exception('Internal error: presence data with weird version')
    elif 'presence' not in conf or 'data' not in conf['presence']:
        raise Exception('Internal error: presence data with no, mm, data')
    elif 'config' not in conf:
        raise Exception('Internal error: presence data with no config')

    # Future version checks and reformatting go here
    return {
        **conf,
        'version': '1.0',
    }


def merge_hashes(current, new):
    """
    Update hashes recursively and report whether anything changed.
    """
    changed = False
    for (k, v) in new.items():
        if k not in current or not isinstance(current[k], type(new[k])):
            current[k] = new[k]
            changed = True
        elif isinstance(current[k], dict):
            if merge_hashes(current[k], new[k]):
                changed = True
        elif current[k] != new[k]:
            current[k] = new[k]
            changed = True
    return changed


def handle_remote_presence(hk, rdebug=lambda s: s):
    hk.set_state('{relation_name}.notify')
    conv = hk.conversation()
    spconf = conv.get_remote('storpool_presence')
    if spconf is None:
        rdebug('no presence data yet')
        return

    rdebug('whee, we got something new from the {key} conversation, '
           'trying to deserialize it'.format(key=conv.key))
    try:
        conf = json.loads(spconf)
        rdebug('got something: type {t}, dict keys: {k}'
               .format(t=type(conf).__name__,
                       k=sorted(conf.keys()) if isinstance(conf, dict)
                       else []))
        if not isinstance(conf, dict):
            rdebug('well, it is not a dictionary, is it?')
            return
        presence_version = conf.get('version')
        if presence_version is None:
            rdebug('no presence data version, ignoring')
            return
        elif not presence_version.startswith('1.'):
            rdebug('unsupported presence data version {ver}, ignoring'
                   .format(ver=presence_version))
            return
        presence = conf.get('presence')
        if not isinstance(presence, dict):
            rdebug('no presence data, just {keys}'
                   .format(keys=','.join(sorted(conf.keys()))))
            return
        elif 'data' not in presence:
            rdebug('invalid presence data format: no "data" member')
            return
        if not isinstance(conf.get('config'), dict):
            rdebug('no config data, just {keys'
                   .format(keys=','.join(sorted(conf.keys()))))
            return

        conf = import_presence(conf)

        stored = unitdata.kv().get(kvdata.KEY_REMOTE_PRESENCE, {})
        changed = merge_hashes(stored, conf)
        if not changed:
            rdebug('nothing changed')
            return
        unitdata.kv().set(kvdata.KEY_REMOTE_PRESENCE, stored)
        hk.set_state('{relation_name}.changed')

    except Exception as e:
        rdebug('oof, could not parse the presence data passed down '
               'the hook: {e}'.format(e=e))


def send_presence_data(rel_name, ext_data={}, rdebug=lambda s: s):
    rdebug('sending presence data along the {name} hook'.format(name=rel_name))
    cfg = spconfig.m()
    data = json.dumps({
        **ext_data,
        'version': '1.0',
        'presence': {
            'data': dict(get_state()[0]),
        },
        'config': {
            'storpool_repo_url': cfg.get('storpool_repo_url'),
            'storpool_version': cfg.get('storpool_version'),
            'storpool_openstack_version':
                cfg.get('storpool_openstack_version'),
            'storpool_conf': cfg.get('storpool_conf'),
        },
    })
    rel_ids = hookenv.relation_ids(rel_name)
    rdebug('- got rel_ids {rel_ids}'.format(rel_ids=rel_ids))
    for rel_id in rel_ids:
        rdebug('  - trying for {rel_id}'.format(rel_id=rel_id))
        hookenv.relation_set(rel_id, storpool_presence=data)
        rdebug('  - done with {rel_id}'.format(rel_id=rel_ids))
    rdebug('- done with the rel_ids')
