#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def fig3d(zdata, xarr=None, yarr=None, xbin=None, ybin=None):
	# zdata[0:ny, 0:nx]: 2-D array
	# xarr(nx): 1-D array storing x-axis (axis-1 of zdata)
	# yarr(ny): 1-D array storing y-axis (axis-0 of zdata)
	# xbin: an INTEGER specifying the number of points to avg (along x-axis)
	# ybin: an INTEGER specifying the number of points to avg (along y-axis)

	if (zdata.ndim != 2):
		print 'array dimension error: zdata[:, :]'
		return None
	(my, mx) = zdata.shape

	if (xarr == None):
		xarr = np.array(range(mx))
	if (yarr == None):
		yarr = np.array(range(my))

	if (xarr.ndim != 1 or yarr.ndim != 1):
		print 'array dimension error: xarr[:], yarr[:]'
		return None

	if (xarr.size != mx or yarr.size != my):
		print 'array size mismatch!'
		return None

	if (xbin == None):	# no binning
		x1d = xarr
		xbin = 1
	else:			# rebin, ignoring trailing incomplete bin
		x1d = xarr[:(mx // xbin) * xbin].reshape(-1, xbin).mean(axis=1)

	if (ybin == None):	# no binning
		y1d = yarr
		ybin = 1
	else:			# rebin, ignoring trailing incomplete bin
		y1d = yarr[:(my // ybin) * ybin].reshape(-1, ybin).mean(axis=1)


	z2d = rebin2d(zdata, ybin, xbin)


	nx = x1d.size
	ny = y1d.size

	x2d = np.array([x1d] * ny)
	y2d = np.array([y1d] * nx).transpose()


	fig = plt.figure()
	ax  = fig.gca(projection='3d')
	ax.scatter(x2d.flatten(), y2d.flatten(), z2d.flatten())

	return fig


def running_mean(x, N, ax=None):
	nd = x.ndim

	if (ax == None):
		if (nd > 1):
			print 'error: did not specify axis for multi-dim array.'
			return None
		acc = np.cumsum(np.insert(x, 0, 0))
		rm = (acc[N:] - acc[:-N]) / N

	else:
		if (ax > nd):
			print 'error: axis specified is larger than array dimension.'
			return None
		acc = np.cumsum(np.insert(x, 0, 0, axis = ax), axis = ax)
		nn = acc.shape[ax]
		rm = (np.delete(acc, range(N), axis = ax) - np.delete(acc, range(nn-N, nn), axis = ax)) / float(N)

	return rm


def rebin2d(x, N0, N1):
	# x[:,:] is a 2-D array
	# (N0, N1) are number of pixels to bin along axis-0 and axis-1 respectively
	if (x.ndim != 2):
		print 'input array needs to be exactly 2-D'
		return None

	(M0, M1) = x.shape

	N0 = min(N0, M0)
	N1 = min(N1, M1)

	nbin0 = M0 // N0
	nbin1 = M1 // N1

	bm = x[:(nbin0 * N0), :(nbin1 * N1)].reshape(nbin0, N0, nbin1, N1).mean(axis=(1,3))

	return bm








