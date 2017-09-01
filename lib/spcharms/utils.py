import time

from charmhelpers.core import hookenv

def rdebug(s, prefix='storpool'):
	data = '[{prefix}] {s}'.format(prefix=prefix, s=s)
	print(data)

	config = hookenv.config()
	def_fname = '/dev/null'
	fname = def_fname if config is None else config.get('storpool_charm_log_file', def_fname)
	if fname != def_fname:
		with open(fname, 'a') as f:
			data_ts = '{tm} {data}'.format(tm=time.ctime(), data=data)
			print(data_ts, file=f)
