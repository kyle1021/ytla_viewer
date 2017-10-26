#!/usr/bin/env python

from ephem import *
import sys
from datetime import datetime
from pyplanet import *


## preparation
inp	= sys.argv[0:]
pg	= inp.pop(0)
now	= datetime.utcnow()    # force UTC
time	= now  # default time
epoch	= '2000'
verbose	= False
singlef	= False
# digital correlator
LO1	= 84.0
LO2	= 5.85
BW	= 1.6
nch	= 1024


## user inputs
usage = '''
usage: %s PLANET [options]

	[options]:
	-t time		# 'now' or 'yyyy-mm-dd HH:MM:SS'
	-e epoch	# '2000', '1950', or something
	-f freq		# output at single frequncy (GHz)
			# (default is to output for all lsb and usb channels and the avg)
	-v		# verbose output

''' % pg

if (len(inp) < 1):
	print usage
	sys.exit()

while (inp):
	arg = inp.pop(0)
	if (arg == '-t'):
		arg = inp.pop(0)
		if (arg != 'now'):
			time = arg
	elif (arg == '-e'):
		epoch = inp.pop(0)
	elif (arg == '-f'):
		fs = float(inp.pop(0))
		singlef = True
	elif (arg == '-v'):
		verbose = True
	else:
		body  = arg



## using the function
b = mloplanet(body.lower(), time, epoch)

if singlef:
	(avg, flux) = planetflux(body.lower(), b.size, fcghz = fs)

else:
	##setup frequency 
	usb = np.linspace(LO1+LO2, LO1+LO2+BW, num=nch) # for usb, the channels have increasing RF
	lsb = np.linspace(LO1+LO2, LO1+LO2-BW, num=nch)	# for lsb, the channels have decreasing RF

	freq = np.array([lsb, usb])

	(avg, flux) = planetflux(body.lower(), b.size, freq)


print 'FluxDensity for ', body.lower(), ' (Jy)'
print avg



if verbose:
	print ""
	print "Coordinates calculated for UTC:"
	print time
	print "Astrometric coordinates:"
	print b.a_ra, b.a_dec
	print "Angular diameter (arcsec):"
	print b.size
	print "FluxDensity in [ [LSB], [USB] ]:"
	print flux
	print "Frequency used:"
	if (singlef):
		print fs
	else:
		print freq


