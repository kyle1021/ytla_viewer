#!/usr/bin/env python
import numpy as np
import sys
import os.path
from loadh5 import *	# import ldoneh5() <-- function; and also (nsb, nch) <-- variables
from drawpdf import *


#-- defaults --
inp	= sys.argv[0:]
pg	= inp.pop(0)
chlim	= [5, 750]		# channel range to avg
tlim	= []			# time    range to avg AND plot (sec)
ys	= 'common'		# amp plot mode
				# 'common' = min/max range of all sub-plots
				# 'indi'   = min/max of individual sub-plots
cylim	= []			# plot range of amp-channel, override ys
tylim	= []			# plot range of amp-time,    override ys
pylim	= [-3.5, 3.5]		# plot range of pha plots (radians)
tset	= False

usage = '''
syntax: %s <All-in-One_H5> [options]

	options are:
	-chr chmin chmax	# override the channel range for averaging ([%d:%d])
	-tr tmin tmax		# set time range in sec
				# note: this determines the range of plot
				# as well as the data to time_average
	-ys <common|indi>	# set y-scale of amp plots to common min/max of all subplots 
				# or individually auto-determined (%s)
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
				tset = True
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


fplt = dname + '/' + fbase



#-- load full data --
print 'loading data'
(time, auto, cross) = ldoneh5(foneh5)
t2 = time - time[0]

## construct array range from time limit
if (tset):
	tw = np.logical_and(t2 >= tmin, t2 <= tmax)
else:
	tw = np.ones(time.size, dtype=bool)

## over-load the arrays according to time range
t2    = t2[tw]
auto  = auto[:,:,:,tw]
cross = cross[:,:,:,tw]



#-- make the plots --


(nsb, na, nch, ndata) = auto.shape
if (na < 3):
	print "closure phase needs at least 3 antennas."
	sys.exit()
nb = na * (na - 1) / 2
(m, n) = findmn(na)
#print na, m, n
w = ['lsb', 'usb']

ch = np.array(range(nch))
close = np.ones((nsb, na, nch, ndata), dtype = complex)

bn = {}
b = -1
for ai in range(na-1):
	for aj in range(ai+1, na):
		b += 1
		bl = '%d%d' % (ai, aj)
		bn[bl] = b

ant = range(na)
sptitle = []
for i in range(na):
	a_use = ant[:]
	a_use.pop(i)
	print len(a_use), a_use
	title = ''

	bl = '%d%d' % (a_use[0], a_use[1])
	title += (bl + ' ')
	print bn[bl]
	close[:,i,:,:] *= cross[:,bn[bl],:,:]

	bl = '%d%d' % (a_use[1], a_use[2])
	title += (bl + ' ')
	print bn[bl]
	close[:,i,:,:] *= cross[:,bn[bl],:,:]

	bl = '%d%d' % (a_use[0], a_use[2])
	title += (bl + '*')
	print bn[bl]
	close[:,i,:,:] *= cross[:,bn[bl],:,:].conjugate()

	sptitle.append(title)


## channel plots (time_avg)
fout = fplt + '.closure-chan.pdf'
plt.figure(figsize = (12,9))
for sb in range(nsb):
	for i in range(na):
		s = i + 1

		plt.subplot(m, n, s)
		plt.plot(ch, np.angle(close[sb,i].mean(axis=1)), ',', label=w[sb])
		#plt.title('closure w/o ant%d' % i)
		plt.title(sptitle[i])
		plt.xlabel('chanel')
		plt.ylabel('closure phase (rad)')
		plt.ylim([-3.5, 3.5])

plt.savefig(fout)
plt.close()


## time plots (chan_avg)
fout = fplt + '.closure-time.pdf'
plt.figure(figsize = (12,9))
for sb in range(nsb):
	for i in range(na):
		s = i + 1

		plt.subplot(m, n, s)
		plt.plot(t2, np.angle(close[sb,i][5:750,:].mean(axis=0)), ',', label=w[sb])
		#plt.title('closure w/o ant%d' % i)
		plt.title(sptitle[i])
		plt.xlabel('time')
		plt.ylabel('closure phase (rad)')
		plt.ylim([-3.5, 3.5])

plt.savefig(fout)
plt.close()

