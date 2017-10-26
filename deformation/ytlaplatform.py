#!/usr/bin/env python
import numpy as np
import os.path


def deform(pntarr, antxy, param_ver):
	'''
	Input:
	------
	pntarr[:,0:2]	list or np.array of [az, el, hp] pointings in deg
	antxy[:,0:1]	np.array of antenna [x, y] positions in m
	                (can also be arbitrary position on the platform to measure deformation)
	param_ver	version of double-saddle params (el, A1, A2, phi1, phi2)
			valid versions:
				2009v1
				2009v2
				2010v2

			Note: params of different hexpols are saved in separate files
				all hexpols of the same version are loaded
				and the params of the hexpol closest to the specified pointing
				are used (no interpolation of parameters in hexpol axis)

	Return:
	------
	deform[0:npt,0:na] and tilt[0:npt,0:na,0:1]
	'''

	pntarr = np.array(pntarr)
	if (len(pntarr.shape) == 1):	    # mainly for when a single pointing is passed
		pntarr = pntarr.reshape(-1,3)
	npt = pntarr.shape[0]
	if (npt * 3 != pntarr.size):
		print 'error reading number of pointings.'
		return None
	print "... number of pointings: %d" % npt

	antxy = np.array(antxy)
	if (len(antxy.shape) == 1):	    # mainly for when a single ant/position is passed
		antxy = antxy.reshape(-1,2)
	na = antxy.shape[0]
	if (na * 2 != antxy.size):
		print 'error reading number of antennas/positions.'
		return None
	print "... number of antennas (or platform samples): %d" % na


	## loading parameters
	hpol = []
	fhpname = []
	if (param_ver == '2009v1'):
		for i in range(5):
			hp = -24 + 12*i
			hpol.append(hp)
			fhpname.append('parameter09XX_hex_%+03d_v1.txt' % (hp))
	elif (param_ver == '2009v2'):
		for i in range(5):
			hp = -24 + 12*i
			hpol.append(hp)
			fhpname.append('parameter09XX_hex_%+03d_v2.txt' % (hp))
	elif (param_ver == '2010v2'):
		for i in range(5):
			hp = -24 + 12*i
			hpol.append(hp)
			fhpname.append('parameter10XX_hex_%+03d_v2.txt' % (hp))
	else:
		print 'error recognizing param_ver.'
		return None

	hpol = np.array(hpol)
	nhp  = hpol.size

        fbase = '/home/corr/kylin/bin/deformation/'
        for i in range(nhp):
                fhpname[i] = fbase + fhpname[i]


	param = []
	for i in range(nhp):
		fhp = fhpname[i]
		print "... loading %s" % fhp
		paramhp = np.loadtxt(fhp, unpack=True)
		param.append(paramhp)
	param = np.array(param)

	print "... done"
	
	## (el, a1, a2, p1, p2) = np.loadtxt(paramfile, unpack=True)
	# el: elevation (in deg) in ascending order
	# a1, a2: amplitude parameters for lengths in mm
	# p1, p2: phase angle parameters in deg

	# deformation:
	# dz = a1 * [(x^2-y^2)*cos(2theta1) + (2xy)*sin(2theta1)]
	#    + a2 * [(x^2-y^2)*cos(2theta2) + (2xy)*sin(2theta2)]
	# with theta1 = az/2 + p1
	# and  theta2 = -az  + p2


	## looping pointings
	dz   = []
	tilt = []
	for p in range(npt):
		(paz, pel, php) = pntarr[p]	# in deg

		#(pa1, pa2, pp1, pp2) = linint(pel, el, a1, a2, p1, p2)
		ihp = np.abs(php - hpol).argmin()	# find the nearest element to php in hpol
		(pa1, pa2, pp1, pp2) = linint(pel, param[ihp])	# interpolate paramets to pel

		theta1 = (paz / 2. + pp1) * np.pi / 180.
		theta2 = (-paz     + pp2) * np.pi / 180.

		## looping antennas / positions
		pdeform = []	# reset for each pointing
		ptilt   = []
		for i in range(na):
			x = antxy[i][0] * 1000.	    # convert to mm
			y = antxy[i][1] * 1000.

			idz = pa1 * ((x**2 - y**2) * np.cos(2.*theta1) + 2.*x*y * np.sin(2.*theta1))
			idz +=pa2 * ((x**2 - y**2) * np.cos(2.*theta2) + 2.*x*y * np.sin(2.*theta2))

			pdeform.append(idz)	    # in mm

			# tx = dz/dx
			tx = 2. * pa1 * ( x * np.cos(2.*theta1) + y * np.sin(2.*theta1))
			tx +=2. * pa2 * ( x * np.cos(2.*theta2) + y * np.sin(2.*theta2))
			# ty = dz/dy
			ty = 2. * pa1 * (-y * np.cos(2.*theta1) + x * np.sin(2.*theta1))
			ty +=2. * pa2 * (-y * np.cos(2.*theta2) + x * np.sin(2.*theta2))

			tx *= -(60. * 180. / np.pi)  # convert to acrmin & invert direction
			ty *= -(60. * 180. / np.pi)  # convert to acrmin
			ptilt.append([tx, ty])

		dz.append(pdeform)
		tilt.append(ptilt)

	return (np.array(dz), np.array(tilt))



def antpos(antconf):
	# pre-defined antenna positions for
	# antconf = '7x0.6', '13x1.4', ...?

	if (antconf == '7x0.6'):
		# 7-element, 0.6m separation
		na = 7
		b0 = 0.7 * np.sqrt(3.) / 2.
		phi0 = 30.	# deg
		antxy = np.zeros([na, 2])   # antxy[0] = [0., 0.] do not need change
		for i in range(1, na):
			phi = np.pi / 180. * (phi0 - 60. * (i - 1))
			antxy[i][0] = b0 * np.cos(phi)
			antxy[i][1] = b0 * np.sin(phi)

	elif (antconf == '13x1.4'):
		# 13-element, 1.4m separation
		na = 13
		# inner ring
		b0 = 1.400
		phi0 = 60.	# deg
		# outer ring
		b1 = b0 * np.sqrt(3.)
		phi1 = 90.	# deg
		antxy = np.zeros([na, 2])   # antxy[0] = [0., 0.] do not need change
		for i in range(1, 7):
			phi = np.pi / 180. * (phi0 - 60. * (i - 1))
			antxy[i][0] = b0 * np.cos(phi)
			antxy[i][1] = b0 * np.sin(phi)

		for i in range(7, na):
			phi = np.pi / 180. * (phi1 - 60. * (i - 7))
			antxy[i][0] = b1 * np.cos(phi)
			antxy[i][1] = b1 * np.sin(phi)

	else:
		print 'invalid antenna configuration specified.'
		return None


	return antxy


def linint(pel, paramhp):
	# linearly interpolate parameters at pel, given (el, a1, a2, p1, p2) for a single hp
	(el, a1, a2, p1, p2) = paramhp

	# find el[i0] <= pel < el[i1]
	# i1 = i0+1 (will not exceed array limit, as long as el is sorted ascending)
	if (pel < el[0]):
		print 'warning: pointing BELOW param elevation range'
		i0 = 0
		i1 = 0
		s0 = 1.
		s1 = 0.
	elif (pel >= el[-1]):
		print 'warning: pointing ABOVE param elevation range'
		i0 = -1
		i1 = -1
		s0 = 1.
		s1 = 0.
	else:
		i0 = (el <= pel).nonzero()[0][-1]
		i1 = i0 + 1
		s0 = (el[i1] - pel) / (el[i1] - el[i0])
		s1  = 1. - s0

	pa1 = s0 * a1[i0] + s1 * a1[i1]
	pa2 = s0 * a2[i0] + s1 * a2[i1]
	pp1 = s0 * p1[i0] + s1 * p1[i1]
	pp2 = s0 * p2[i0] + s1 * p2[i1]

	return (pa1, pa2, pp1, pp2)



def platsamp(spacing = None):
	'''
	return a sample of positions to represent the platform
	unit in m (same as antpos())
	'''
	## define edge of hexapod
	rou = 3.
	rin = rou * np.sqrt(3.) / 2.

	## define sampling density
	if (spacing):
		dx = spacing
		dy = spacing
	else:
		dx = 0.2
		dy = 0.2

	## define over samples
	g = np.mgrid[-rou:(rou+0.001):dx, -rou:(rou+0.001):dy]    # [-rou:rou] inclusive
	(nd, nx, ny) = g.shape
	samp = np.zeros([nx, ny, 2])
	samp[:,:,0] = g[0,:,:]
	samp[:,:,1] = g[1,:,:]
	samp = samp.reshape(-1, 2)
	srad = np.sqrt(samp[:,0]**2 + samp[:,1]**2)
	sang = np.arctan2(samp[:,1], samp[:,0])	    # in rad

	## define masks (by six triangle regions)
	mask = (srad <= rou)
	for i in range(6):
		ang = np.pi / 6. + i * np.pi / 3.
		univec = np.array([np.cos(ang), np.sin(ang)])
		imask = (np.dot(samp, univec) < rin)

		mask = np.logical_and(mask, imask)

	return samp[mask]


