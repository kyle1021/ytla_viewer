#!/usr/bin/env python
import numpy as np
import h5py
import sys, os.path
from datetime import datetime

nsb = 2		# fixed num. of sidebands ('lsb', 'usb')
nch = 1024	# fixed num. of channels



def ldcorr(fname, na):
    nb = na * (na-1) / 2

    if (fname.endswith('.')):
	fname.rstrip('.')
    elif (fname.endswith('.timestamp')):
	fname.rstrip('.timestamp')

    ftime = fname + '.timestamp'

    if (os.path.isfile(ftime)):
	print 'use existing .timestamp file'
    else:
	print 'no existing .timestamp file'
	print 'will use ad hoc time info (1 sec/pt)'

    dname = os.path.dirname(fname)
    if (dname == ''):
	dname = '.'
    fbase = fname


    print '... ', datetime.now().isoformat()


    #-- determine data length --
    aname = dname + '/' + fbase + '.%s.%s.h5' % ('lsb', 'auto')
    ha = h5py.File(aname, 'r')
    bname = 'auto%d%d' % (0, 0)
    arr = np.array(ha.get(bname))
    (nch, ndata) = arr.shape
    ha.close()

    #-- load data --
    if (os.path.isfile(ftime)):
	time = np.loadtxt(ftime)
    else:
	time = np.arange(ndata)
    

    w = ['lsb', 'usb']
    auto  = np.zeros((nsb, na, nch, ndata))
    cross = np.zeros((nsb, nb, nch, ndata), dtype=complex)
    for s in range(nsb):
	b = -1

	xtype = 'auto'
	aname = dname + '/' + fbase + '.%s.%s.h5' % (w[s], xtype)
	print aname, '--> ', os.path.isfile(aname)
	ha = h5py.File(aname, 'r')
	xtype = 'cross'
	cname = dname + '/' + fbase + '.%s.%s.h5' % (w[s], xtype)
	print cname, '--> ', os.path.isfile(cname)
	hc = h5py.File(cname, 'r')

	for i in range(na):
	    bname = 'auto%d%d' % (i, i)
	    arr = np.array(ha.get(bname))
	    auto[s, i] = arr
		    
	    for j in range(i+1, na):
		b += 1
		bname = '/cross%d%d' % (i, j)
		arr = np.array(hc.get('%s/real' % bname))
		cross[s, b].real = arr
		arr = np.array(hc.get('%s/imag' % bname))
		cross[s, b].imag = arr

	ha.close()
	hc.close()

    print '... ', datetime.now().isoformat()
    return time, auto, cross


def wtoneh5(h5name, time, auto, cross):
	# write out the full dataset into an All-in-One h5 file
	print '... ', datetime.now().isoformat()

	s = auto.shape
	#nsb	= s[0]	# already determined
	na	= s[1]
	# nch	= s[2]	# already determined
	ndata	= s[3]

	nb = na * (na-1) / 2

	#with h5py.File(h5name, 'w') as f:
	f = h5py.File(h5name, 'w')

	f.attrs['na']	= na
	f.attrs['nb']	= nb
	f.attrs['nsb']	= nsb
	f.attrs['nch']	= nch
	f.attrs['ndata']= ndata

	print '...  timestamp'
	f.create_dataset('timestamp', data = time)
	print '...  auto-corr (real)'
	f.create_dataset('auto',      data = auto)
	print '...  cross-corr (complex)'
	f.create_dataset('cross',     data = cross)

	f.close()

	print '... ', datetime.now().isoformat()


def ldoneh5(h5name):
	# load the dataset from All-in-one h5 file
	print '... ', datetime.now().isoformat()

	with h5py.File(h5name, 'r') as f:
		#na 	= f.attrs['na']
		#nb 	= f.attrs['nb']
		#nsb	= f.attrs['nsb']
		#nch	= f.attrs['nch']
		#ndata	= f.attrs['ndata']

		print '...  timestamp'
		time = np.array(f.get('timestamp'))
		print '...  auto-corr (real)'
		auto  = np.array(f.get('auto'))
		print '...  cross-corr (complex)'
		cross = np.array(f.get('cross'))

	print '... ', datetime.now().isoformat()
	return time, auto, cross


def adoneh5(h5name, darray, dname):
	#print datetime.now().isoformat()

	with h5py.File(h5name, 'a') as f:
		print '... ', dname
		f.create_dataset(dname, data = darray)

	#print datetime.now().isoformat()


def newraw(rawh5, na):
	# when rawh5 (i.e. .raw.oneh5) does not exist, create a new one from .timestamp file
	# update: can create a new one from basename (without .timestamp)

	if (rawh5.endswith('.raw.oneh5')):
		base = rawh5.rstrip('.raw.oneh5')
	else:
		print 'expecting rawh5 file ends with ".raw.oneh5"'
		return None

	(time, auto, cross) = ldcorr(base, na)

	print 'output to %s' % rawh5
	wtoneh5(rawh5, time, auto, cross)


## self-test
if (False):
	from subprocess import call
	call('date')
	ftime = '161102-Jup2/2016_Nov_02_22_18_35.corr1k.timestamp'
	(time, auto, visr, visi) = ldcorr(ftime, 4)
	print time.shape, auto.shape, visr.shape, visi.shape
	call('date')


if (__name__ == '__main__'):


    inp = sys.argv[0:]
    pg  = inp.pop(0)
    usage = '''
    program needs two arguments.

    %s <file_base> <na>

	<file_base> = something like './data/2017_Oct_26_03_35_27.ytla'
	if the .h5 files are in the current directory, the path can be omitted

    ''' % pg

    if (len(inp) >= 2):
	fname = inp.pop(0)
	na = int(inp.pop(0))

	if (fname.endswith('.timestamp')):
	    fname.rstrip('.timestamp')

	fout = fname + '.raw.oneh5'
	print 'reading data ...'
	time, auto, cross = ldcorr(fname, na)
	print 'writing data ...'
	wtoneh5(fout, time, auto, cross)

    else:
	print usage	


