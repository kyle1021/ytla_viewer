#!/usr/bin/env python
import numpy as np
import h5py
import os.path
from datetime import datetime

nsb = 2		# fixed num. of sidebands ('lsb', 'usb')
nch = 1024	# fixed num. of channels



def ldcorr(ftime, na):
	nb = na * (na-1) / 2

	if (os.path.isfile(ftime)):
		pass
	else:
		print 'ldcorr: Error finding <timestamp_file> %s' % ftime
		return None

	dname = os.path.dirname(ftime)
	if (dname == ''):
		dname = '.'
	fname = os.path.basename(ftime)
	if (fname.endswith('.timestamp')):
		fbase = fname.rstrip('.timestamp')
	else:
		fbase = fname
		print 'Warning: non-standard <timestamp> filename detected.'


	print '... ', datetime.now().isoformat()

	#-- load data --
	time = np.loadtxt(ftime)
	ndata = len(time)
	

	w = ['lsb', 'usb']
	auto  = np.zeros((nsb, na, nch, ndata))
	cross = np.zeros((nsb, nb, nch, ndata), dtype=complex)
	for s in range(nsb):
		b = -1
		for i in range(na):
			bname = '%d%d' % (i, i)
			xtype = 'auto'
			xname = dname + '/' + fbase + '.%s.%s.%s.h5' % (bname, w[s], xtype)
			print xname, '--> ', os.path.isfile(xname)
			try:
				hf = h5py.File(xname, 'r')
				arr = np.array(hf.get('fullData/real'))
				auto[s, i] = arr
				hf.close()
			except IOError:
				pass
				
			for j in range(i+1, na):
				b += 1
				bname = '%d%d' % (i, j)
				xtype = 'cross'
				xname = dname + '/' + fbase + '.%s.%s.%s.h5' % (bname, w[s], xtype)
				print xname, '--> ', os.path.isfile(xname)
				try:
					hf = h5py.File(xname, 'r')
					arr = np.array(hf.get('fullData/real'))
					cross[s, b].real = arr
					arr = np.array(hf.get('fullData/imag'))
					cross[s, b].imag = arr
					hf.close()
				except IOError:
					pass


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

	if (rawh5.endswith('.raw.oneh5')):
		base = rawh5.rstrip('.raw.oneh5')
	else:
		print 'expecting rawh5 file ends with ".raw.oneh5"'
		return None

	rawts = base + '.timestamp'

	if (os.path.isfile(rawts)):
		print 'reading from %s' % rawts
		(time, auto, cross) = ldcorr(rawts, na)
	else:
		print 'could not find timestamp file %s' % rawts
		return None

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



