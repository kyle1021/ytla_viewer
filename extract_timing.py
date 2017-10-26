#!/usr/bin/env python

import numpy as np
import sys, os.path
import h5py
from datetime import datetime

inp   = sys.argv[0:]
pg    = inp.pop(0)
do_ts = False

usage = '''
usage %s <tcs_ctrl.sched> [options]


    <tcs_ctrl.sched>	including the relative path to the file
			tcs_ctrl.tab will be needed as well
			and it should be located in the same dir
    [options] are
    -ts <corr_file_prefix> <T_int>
			the filename common part, in the format:
			2017_Aug_24_01_34_41.ytla7
			a relative path can be included
			a timestamp file will be saved as
			<corr_file.prefix>.timestamp

			<T_int> is the integration time per data point

			Note: without -ts option, there will be no timestamp file

''' % pg

if (len(inp) < 1):
    print usage
    sys.exit()

fsch = inp.pop(0)
while (len(inp) > 0):
    k = inp.pop(0)
    if (k == '-ts'):
	try:
	    prefix = inp.pop(0).rstrip('.')
	    tint   = float(inp.pop(0))
	except:
	    print '-ts needs two arguements'
	    print usage
	    sys.exit()
	fcorr  = prefix + '.lsb.cross.h5'
	if (os.path.isfile(fcorr)):
	    do_ts = True
	    fts   = prefix + '.timestamp'
	else:
	    print 'can not find correlation data:', fcorr
	    print 'skip generating timestamp file'
	    do_ts = False


if (not os.path.isfile(fsch)):
    print 'error finding: ', fsch
    sys.exit()
elif (not fsch.endswith('.tcs_ctrl.sched')):
    print 'not a tcs_ctrl.sched file?'
    sys.exit()
ftab = fsch.rstrip('.sched') + '.tab'
obsdate = os.path.basename(fsch).rstrip('.tcs_ctrl.sched')



with open(fsch, 'r') as fin:
    print fin.read()
print ''
sid = raw_input('select sched unit id (1st column): ')
sid = int(sid)
if (do_ts):
    ftxt = prefix + '.sch_timing.txt'
else:
    ftxt = obsdate + '.s%d' % sid + '_timing.txt'


data = np.loadtxt(ftab, usecols=(0,4,5), unpack=True)
tstring = np.loadtxt(ftab, usecols=(2,3), unpack=True, dtype='str')
w = (data[0] == sid)

stamp0 = tstring[0][w][0]
print 'stamp0 =', stamp0
hh, mm, ss = stamp0.split(':')
t0 = 3600. * float(hh) + 60. * float(mm) + int(float(ss))

datestr = '%s %s:%s:%s' % (obsdate, hh, mm, int(float(ss)))
dtobj = datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
epoch = float(dtobj.strftime('%s'))             # convert to linux time
print "linux epoch = ", epoch


with open(ftxt, 'w') as fout:
    for t1, t2, s1, s2 in zip(data[1][w], data[2][w], tstring[0][w], tstring[1][w]):
	print >> fout, '%5.0f   %5.0f   %s   %s' % (t1-t0, t2-t0, s1, s2)


if (do_ts):
    try:
	hd1 = h5py.File(fcorr, 'r')
	d = hd1.get('/cross01/real')
	(nch, npt) = d.shape
    except:
	print 'error accessing file:', fcorr
	sys.exit()

    with open(fts, 'w') as f1:
	for i in range(npt):
	    t = epoch + tint * float(i)
	    print >> f1, '%.3f' % t


