#!/usr/bin/env python
import numpy as np
import sys
import os.path
from subprocess import call
from loadh5 import *
from scipy import signal


#-- defaults --
inp 	= sys.argv[0:]
pg  	= inp.pop(0)
nch	= 1024
nsb	= 2
na  	= 7
nb  	= na * (na-1) / 2
chmin	= 20
chmax	= 760
loadcal	= True
# default to phase-cal only for now
phasecal = True
gaincal  = True
caltype  = '.'
caltr	 = 'all'
calcr	 = 'default'
gsigma	 = 0.		# default no gaussian spectral filtering 
flux_jy	 = 0.		# default no flux cal.


#-- usage --
usage = '''
this script loads raw data and calibration data sets and perform phase calibration
(zeroing phase across bandpass for the calibration data set)
the output is cal_vis.amp (channel avg) as a function of time

syntax %s <raw_oneh5_file> <cal_oneh5_file> [options]

	special case: if <cal_oneh5_file> == 'none' or 'null'
	output raw_vis.amp with no calibration

	options are:
	-(no)pcal	# toggle (phase-cal = %r)
	-(no)gcal	# toggle (gain-cal  = %r)
	-fcal flux_jy	# normalize to flux in Jy

	-caltr t1 t2	# limit the time range of calibrator data to [t1:t2]
			# bandpass is averaged within this time range

	-calcr c1 c2	# normalize the bandpass between [c1:c2]

	-filter sigma	# sigma for Gaussian spectral filtering (%d channels)


''' % (pg, phasecal, gaincal, gsigma)

if (len(inp) < 2):
	print usage
	#sys.exit()
	line = raw_input('command line arguements:\n')
	inp = line.split()


#-- user inputs --
while(inp):
	arg = inp.pop(0)
	if (arg == '-pcal'):
		phasecal = True
	elif (arg == '-nopcal'):
		phasecal = False
	elif (arg == '-gcal'):
		gaincal  = True
	elif (arg == '-nogcal'):
		gaincal  = False
	elif (arg == '-fcal'):
		try:
		    flux_jy = float(inp.pop(0))
		except ValueError:
		    print 'error getting flux, ignoring flux cal.'
	elif (arg == '-caltr'):
		try:
		    t1 = float(inp.pop(0))
		    t2 = float(inp.pop(0))
		    if (t1 < t2):
			caltr = 'user'
		except ValueError:
		    print 'cal time range error.'
	elif (arg == '-calcr'):
		try:
		    c1 = int(inp.pop(0))
		    c2 = int(inp.pop(0))
		    if (c1 < c2):
			calcr = 'user'
			chmin = c1
			chmax = c2
		except ValueError:
		    print 'cal channel range error.'
		    print 'fall back to default range'
	elif (arg == '-filter'):
		try:
		    gsigma = float(inp.pop(0))
		except ValueError:
		    print 'invalid sigma value for Gaussian spectral filter.'
		    print 'ignore filtering'
		    gsigma = 0.
	else:
		rawh5 = arg
		calh5 = inp.pop(0)

if (os.path.isfile(rawh5)):
	print 'using raw data: %s' % rawh5
else:
	print 'error finding raw data: %s' % rawh5
	rawts = rawh5.rstrip('.raw.oneh5') + '.timestamp'
	if (os.path.isfile(rawts)):
		print 'converting from timestamp file %s' % rawts
		newraw(rawh5, na)
	else:
		sys.exit()

rawdir = os.path.dirname(rawh5)
rawdir = rawdir if (rawdir != '') else '.'
rawname = os.path.basename(rawh5)
if (rawname.endswith('.oneh5')):
	rawbase = rawname.rstrip('.oneh5')
else:
	rawbase = rawname


if (calh5 == 'none' or calh5 == 'null'):
	loadcal = False
	outadj = '.null'
elif (calh5 == 'self'):
	outadj = '.self'
elif (os.path.isfile(calh5)):
	print 'using cal data: %s' % calh5
	outadj = ''
else:
	print 'error finding cal data: %s' % calh5
	sys.exit()


caltype = caltype + 'p' if (phasecal) else caltype
caltype = caltype + 'g' if (gaincal)  else caltype


if (rawbase.endswith('.raw')):
	outbase = rawbase.rstrip('.raw') + outadj + caltype + '.cal'
else:
	outbase = rawbase + outadj + caltype + '.cal'

outh5 = rawdir + '/' + outbase + '.oneh5'


#-- loading data --
(rawtime, rawauto, rawcross) = ldoneh5(rawh5)
nraw = len(rawtime)

if (loadcal):
	if (calh5 == 'self'):
		(caltime, calauto, calcross) = (rawtime, rawauto, rawcross)
	else:
		(caltime, calauto, calcross) = ldoneh5(calh5)
	#ncal = len(caltime)
	(nsb, nb, nch, ncal) = calcross.shape
	# calcross has shape of (nsb, nb, nch, ncal)
	# with nsb = 2, nch = 1024 defined in loadh5.py

	## time avg cal data to get a single phassband (not normalized yet)
	if (caltr == 'all'):
	    tw = np.ones(caltime.size, dtype='bool')
	elif (caltr == 'user'):
	    run = True
	    t = caltime - caltime[0]
	    if (t1 > t[-1]):
		run = False
	    if (t2 < t[0]):
		run = False
	    if (run):
		tw = np.logical_and(t>=t1, t<=t2)
	    else:
		print 'warning: invalid cal time range. use all range.'
		tw = np.ones(caltime.size, dtype='bool')
	    
	avgcal = calcross[:,:,:,tw].mean(axis = 3)

	## perform spectral smoothing if a Gaussian sigma is provided
	if (gsigma > 0.):
	    print 'smoothing...'
	    glen = 6. * gsigma
	    win = signal.gaussian(glen, gsigma)
	    win /= win.sum()
	    for s in range(nsb):
		for b in range(nb):
		    avgcal[s,b] = signal.convolve(avgcal[s,b], win, 'same')

	## define normalization factor in the channel range specified
	norm = np.abs(avgcal[:,:,chmin:chmax].mean(axis=2))

	## the (relative) passband
	for i in range(nch):
		avgcal[:,:,i] = avgcal[:,:,i] / norm[:,:]

	if (phasecal == False):
		avgcal = np.abs(avgcal) 

	if (gaincal  == False):
		avgcal = avgcal / np.abs(avgcal)


else:
	avgcal = np.ones((nsb, nb, nch), dtype=complex)
	norm   = np.ones((nsb, nb))


## flux cal
if (flux_jy > 0.):
    for i in range(nch):
	avgcal[:,:,i] = avgcal[:,:,i] * norm[:,:] / flux_jy
    norm = np.ones_like(norm) * flux_jy


#-- passband cal --
## in-placecal instead of copy array to save memory
for i in range(nraw):
	rawcross[:,:,:,i] = rawcross[:,:,:,i] / avgcal[:,:,:]


if (outadj != 'null'):
	print 'saving calibrated vis in %s' % outh5
	wtoneh5(outh5, rawtime, rawauto, rawcross)
	print 'adding relative passband'
	#adoneh5(outh5, avgcal, 'passband')
	print 'adding normalzation of passband (not used in passband cal)'
	#adoneh5(outh5, norm, 'gain')
	with h5py.File(outh5, 'a') as f:
		dpb = f.create_dataset('passband', data = avgcal)
		dpb.attrs['calsrc'] = calh5
		dpb.attrs['phasecal'] = phasecal
		dpb.attrs['gaincal']  = gaincal
		dg  = f.create_dataset('gain', data = norm)
		dg.attrs['chmin'] = chmin
		dg.attrs['chmax'] = chmax



#-- channel avg --
rawcross_ca = rawcross[:,:,chmin:chmax,:].mean(axis = 2)



#-- output --
ascdir = rawdir + '/' + 'ascii' + outadj + caltype
call(['mkdir', '-p', ascdir])
sb	= ['lsb', 'usb']

print 'saving ascii outputs'
for s in range(nsb):
	b = -1
	for i in range(na-1):
		for j in range(i+1, na):
			b += 1
			outname = ascdir + '/' + rawbase.rstrip('.raw') + '.%d%d.' % (i, j) + sb[s] + '_time'

			f = open(outname, 'w')
			for k in range(nraw):
				print >> f, np.abs(rawcross_ca[s, b, k])
			f.close()

print 'done.'

