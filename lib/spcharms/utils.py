import time

def rdebug(s, prefix='storpool'):
	data = '[{prefix}] {s}'.format(prefix=prefix, s=s)
	print(data)

	# FIXME: make this conditional, I guess?
	with open('/tmp/storpool-charms.log', 'a') as f:
		data_ts = '{tm} {data}'.format(tm=time.ctime(), data=data)
		print(data_ts, file=f)
