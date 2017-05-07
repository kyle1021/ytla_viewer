#!/usr/bin/env python
import numpy as np
import sys
import os.path
from loadh5 import *	# import ldoneh5() <-- function; and also (nsb, nch) <-- variables
from drawpdf import *


#-- defaults --
inp	= sys.argv[0:]
pg	= inp.pop(0)
na	= 4
nb	= na * (na-1) / 2
chlim	= [5, 750]		# channel range to avg
tlim	= []			# time    range to avg AND plot (sec)
ys	= 'common'		# amp plot mode
				# 'common' = min/max range of all sub-plots
				# 'indi'   = min/max of individual sub-plots
cylim	= []			# plot range of amp-channel, override ys
tylim	= []			# plot range of amp-time,    override ys
pylim	= [-3.5, 3.5]		# plot range of pha plots (radians)
logy	= False			# whether to plot amp plots in log-scale


usage = '''
syntax: %s <All-in-One_H5> [options]

	options are:
	-chr chmin chmax	# override the channel range for averaging ([%d:%d])
	-tr tmin tmax		# set time range in sec
				# note: this determines the range of plot
				# as well as the data to time_average
	-ys <common|indi>	# set y-scale of amp plots to common min/max of all subplots 
				# or individually auto-determined (%s)
	-logy			# set y-scale of amp-channel plots to log-scale
	-cyr cymin cymax	# set a fixed yrange for amp-channel plots
	-tyr tymin tymax	# set a fixed yrange for amp-time plots

''' % (pg, chlim[0], chlim[1], ys)


#-- get inputs --
if (len(inp) < 1):
	print usage
	#sys.exit()
	line = raw_input('command line arguements:\n')
	inp = line.split()

while (inp):
	arg = inp.pop(0)
	if (arg == '-chr'):
		try:
			chmin = int(inp.pop(0)) 
			chmax = int(inp.pop(0))
			if (chmin >= 0 and chmax <= nch):
				chlim = [chmin, chmax]
			else:
				print "channel range invalid. using defaults = [%d:%d]" % (chmin, chmax)
		except ValueError:
			print "error reading channel range"
	elif (arg == '-tr'):
		try:
			tmin = float(inp.pop(0))
			tmax = float(inp.pop(0))
			if (tmin < 0.):
				tset = False
				print 'input time range invalid. using defaults = "full"'
			else:
				tlim = [tmin, tmax]
		except ValueError:
			print "error reading time range"
	elif (arg == '-ys'):
		ys = inp.pop(0)
		if (ys == 'common' or ys == 'indi'):
			pass
		else:
			ys = 'common'
			print 'input y-scale invalid. using defaults = %s' % ys
	elif (arg == '-cyr'):
		try:
			cymin = float(inp.pop(0))
			cymax = float(inp.pop(0))
			cylim = [cymin, cymax]
		except ValueError:
			print 'amp-chan yrange invalid. using default range.'
	elif (arg == '-tyr'):
		try:
			tymin = float(inp.pop(0))
			tymax = float(inp.pop(0))
			tylim = [tymin, tymax]
		except ValueError:
			print 'amp-time yrange invalid. using default range.'
	elif (arg == '-logy'):
		logy = True
	else:
		foneh5 = arg
		if (os.path.isfile(foneh5)):
			print 'using data: %s' % foneh5
		else:
			print 'error finding file: %s' %foneh5


dname = os.path.dirname(foneh5)
if (dname == ''):
	dname = '.'
fname = os.path.basename(foneh5)
if (fname.endswith('.oneh5')):
	fbase = fname.rstrip('.oneh5')
else:
	fbase = fname

if (logy):
	fplt = dname + '/' + fbase + '.log'
else:
	fplt = dname + '/' + fbase + '.lin'





#-- load full data --
print 'loading data'
(time, auto, cross) = ldoneh5(foneh5)




#-- make the plots --

fout = fplt + '.pdf'

corr2pdf(fout, time, auto, cross,
	ys = ys, logy = logy,
	tlim = tlim, chlim = chlim,
	cylim = cylim, tylim = tylim
)


