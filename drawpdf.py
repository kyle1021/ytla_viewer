#!/usr/bin/env python
import numpy as np
### default backend (TkAgg) is capable of screen and png/pdf file outputs
### the two lines below are thus not necessary
##import matplotlib
##matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import sys




def corr2pdf(fout, time, auto, cross, **kwargs):
	# numpy arrays:
	#	time(ndata), float
	# 	auto(nsb, na, nch, ndata), float
	# 	cross(nsb, nb, nch, ndata), complex

	(nsb, na, nch, ndata) = auto.shape
	nb = na * (na-1) / 2


	# the defaults
	valid_op = ['tlim', 'chlim', 'cylim', 'tylim', 'ys', 'logy', 'pylim', 'figsize', 'gs']
	for k in kwargs:
		if (not(k in valid_op)):
			print 'error: option %s is not defined.' % k 
			return None

	opts = {
		'tlim'	: kwargs.get('tlim', []),		# time range to avg/plot
		'cylim'	: kwargs.get('cylim', []),		# plot range of amp-channel
		'tylim'	: kwargs.get('tylim', []),		# plot range of amp-time
	}
	ys 	= kwargs.get('ys', 'common')			# 'common' or 'indi'
	logy	= kwargs.get('logy', False)			# y-axis log-scale or not
	chlim	= kwargs.get('chlim', [5, 750])			# channel range to avg
	pylim	= kwargs.get('pylim', [-3.5, 3.5])		# plot range of phase
	figinch = kwargs.get('figsize', (10, 7.5))		# fig size in (x, y) inches
								# (dpi = 100?)
	gs	= kwargs.get('gs', 0.)				# gain slope to multiply (in dB across ~1000ch)

	if (opts['tlim']):
		print '... tset = True'
		tset = True
		tmin = opts['tlim'][0]
		tmax = opts['tlim'][1]
	else:
		tset = False
	if (opts['cylim']):
		print '... cyset = True'
		cyset = True
		cymin = opts['cylim'][0]
		cymax = opts['cylim'][1]
	else:
		cyset = False
	if (opts['tylim']):
		print '... tyset = True'
		tyset = True
		tymin = opts['tylim'][0]
		tymax = opts['tylim'][1]
	else:
		tyset = False



	t2 = time[:] - time[0]		# relative time
	ch = np.array(range(nch))	# channel number

	## construct array range from time limit
	if (tset):
		tw = np.logical_and(t2 >= tmin, t2 <= tmax)
	else:
		tw = np.ones(time.size, dtype=bool)

	## over-load the arrays according to time range
	t2    = t2[tw]
	auto  = auto[:,:,:,tw]
	cross = cross[:,:,:,tw]


	## apply gain slope correction
	if (gs != 0.):
	    gcal = np.ones((1,1,nch,1))
	    gcal[0,0,:,0] = 10**(ch * gs/10./float(nch))
	    cross *= gcal
	    


	## averaging
	auto_ta  = auto.mean(axis=3)
	cross_ta = cross.mean(axis=3)
	if (ys == 'common' and not(cyset)):	# do not override the user-set range
		cymax = np.abs(cross_ta).max()
		if (logy):
			cymin = np.abs(cross_ta).min()
		else:
			cymin = 0.
		cyset = True

	auto_ca  = auto[:,:,chlim[0]:chlim[1],:].mean(axis=2)
	cross_ca = cross[:,:,chlim[0]:chlim[1],:].mean(axis=2)
	if (ys == 'common' and not(tyset)):	# do not override the user-set range
		tymax = np.abs(cross_ca).max()
		if (logy):
			tymin = np.abs(cross_ca).min()
		else:
			tymin = 0.
		tyset = True



	#-- make plots --
	#fout = fplt + '.pdf'
	pdf  = PdfPages(fout)


	#-- plot auto --
	sb = ['lsb', 'usb']	# sidebands
	(m, n) = findmn(na)	# na = 4 subplots

	### channel plot (time avg) ###
	print 'plotting auto channel plots'
	title = fout + ' (auto, amp-chan)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		for a in range(na):
			sub = a + 1
			p1 = plt.subplot(m, n, sub)

			plt.plot(ch, auto_ta[s, a], ',', label=sb[s])
			plt.title('Ant ' + str(a))
			plt.xlabel('channel')
			plt.ylabel('<vis.amp>_tavg')
			if (logy):
				p1.set_yscale('log')

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()

	### time plot (channel avg) ###
	print 'plotting auto time plots'
	title = fout + ' (auto, amp-time)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		for a in range(na):
			sub = a + 1
			p1 = plt.subplot(m, n, sub)

			plt.plot(t2, auto_ca[s, a], ',', label=sb[s])
			plt.title('Ant ' + str(a))
			plt.xlabel('time (sec)')
			plt.ylabel('<vis.amp>_chavg')

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()



	#-- plot cross --
	(m, n) = (na-1, na-1)

	### channel plot ###
	print 'plotting cross channel plots'

	title = fout + ' (cross, amp-channel)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		b = -1
		shift = 0
		for i in range(na-1):
			shift += i
			for j in range(i+1, na):
				b += 1
				sub = 1 + b + shift
				
				p1 = plt.subplot(m, n, sub)

				plt.plot(ch, np.abs(cross_ta[s, b]), '-', label=sb[s])
				plt.title('Baseline ' + str(i) + str(j))
				plt.xlabel('channel')
				plt.ylabel('<vis.amp>_tavg')
				if (cyset):
					plt.ylim(cymin, cymax)
				if (logy):
					p1.set_yscale('log')

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()

	title = fout + ' (cross, pha-channel)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		b = -1
		shift = 0
		for i in range(na-1):
			shift += i
			for j in range(i+1, na):
				b += 1
				sub = 1 + b + shift
				
				p1 = plt.subplot(m, n, sub)

				plt.plot(ch, np.angle(cross_ta[s, b]), ',', label=sb[s])
				#ax = plt.gca()
				#ax.set_ylim(pylim)
				plt.title('Baseline ' + str(i) + str(j))
				plt.xlabel('channel')
				plt.ylabel('<vis.pha>_tavg')
				plt.ylim(pylim)

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()


	### time plots ###
	print 'plotting cross time plots'

	title = fout + ' (cross, amp-time)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		b = -1
		shift = 0
		for i in range(na-1):
			shift += i
			for j in range(i+1, na):
				b += 1
				sub = 1 + b + shift
				
				p1 = plt.subplot(m, n, sub)

				plt.plot(t2, np.abs(cross_ca[s, b]), '-', label=sb[s])
				plt.title('Baseline ' + str(i) + str(j))
				plt.xlabel('time (sec)')
				plt.ylabel('<vis.amp>_chavg')
				if (tyset):
					plt.ylim(tymin, tymax)
				#if (logy):
				#	p1.set_yscale('log')

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()


	title = fout + ' (cross, pha-time)'
	for s in range(nsb):
	#for s in range(1,2):

		f1 = plt.figure(1, figsize=figinch)	# for png backends, dpi is fixed at 100?
		b = -1
		shift = 0
		for i in range(na-1):
			shift += i
			for j in range(i+1, na):
				b += 1
				sub = 1 + b + shift
				
				p1 = plt.subplot(m, n, sub)

				plt.plot(t2, np.angle(cross_ca[s, b]), ',', label=sb[s])
				#ax = plt.gca()
				#ax.set_ylim(pylim)
				plt.title('Baseline ' + str(i) + str(j))
				plt.xlabel('time (sec)')
				plt.ylabel('<vis.pha>_chavg')
				plt.ylim(pylim)

		plt.legend(loc = 'upper right')
		plt.suptitle(title)

	pdf.savefig(f1)
	plt.close()


	pdf.close()




def findmn(N):
	# find the minimum (m, n) so that 
	# 	m * n >= N
	# 	m = n or (n+1)

	m = 1
	n = 1
	while (m * n < N):
		if (m == n):
			m = n + 1
		else:
			n = n + 1
			m = n

	return m, n



