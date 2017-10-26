#!/usr/bin/env python
# calculates the apparent (date) coordinates of planets
# for Saturn, also can calculate the ring inclination (earth_tilt)
# 2011/06/02

import sys
import numpy as np
from ephem import *
from datetime import datetime
#from astropy.constants import c, h, k_B
c   = 299792458.0       # speed of light SI
h   = 6.62606957e-34    # Planck constant SI
k_B = 1.3806488e-23     # Boltzmann constant SI


def mloplanet(body, time, epoch):
	## define planet to calculate
	if   (body.lower() in 'jupiter'):
	    b = Jupiter()
	elif (body.lower() in 'saturn' ):
	    b = Saturn()
	elif (body.lower() in 'mars'   ):
	    b = Mars()
	elif (body.lower() in 'neptune'):
	    b = Neptune()
	elif (body.lower() in 'uranus'):
	    b = Uranus()
	elif (body.lower() in 'venus'  ):
	    b = Venus()
	elif (body.lower() in 'pluto'  ):
	    b = Pluto()
	elif (body.lower() in 'mercury'):
	    b = Mercury()
	elif (body.lower() in 'moon'   ):
	    b = Moon()
	elif (body.lower() in 'sun'    ):
	    b = Sun()
	else:
	    print 'unknown PLANET =', body
	    sys.exit()


	## define observer
	# Mauna Loa Observatory site information taken from AMiBA Wiki
	mlo = Observer()
	mlo.long	= '-155.5753'
	mlo.lat		= '+19.5363'
	mlo.elevation	= 3426.0
	mlo.temp	= 0	    # set temp and pressure to 0 to ignore atmosphere correction
	mlo.pressure	= 0
	mlo.date	= time	    # this is variable now
	# can omit epoch if using J2000 (is the default)
	mlo.epoch	= epoch
	#mlo.epoch	= '2000/1/1.5'

	# Note:
	# epoch matters only if output is astrometric coordinates (not apparent coordinates)
	# astrometric coordinates = a_ra, a_dec (will use epoch setting) --> geocentric
	# apparent geocentric     = g_ra, g_dec (will ignore epoch setting)
	# apparent topocentric    = ra, dec     (also will ignore epoch settting)


	## start calculation for each line
	b.compute(mlo)

	# (b.ra, b.dec) = apparent topocentric
	# (b.a_ra, b.a_dec) = astrometric
	# b.size = angular diameter
	# b.earth_tilt = ring opening angle toward earth (for Saturn only?)

	return b


## The 3mm disc brightness temperature listed in MIR cookbook.
## References: 
##  Ulich 1981 A.J.,86,1619,
##  Griffen 1986 Icarus 65,244
##  Hildebrand 1985 Icarus,64,64
##  Orton 1986,Icarus 67,289
##  Muhleman&Berge 1991
##
## Update: 
##  for Jupiter, Saturn, Mars, Uranus, Neptune
##  W-band brightness temperature from WMAP-7 (Weiland+2011) are used
Tdisc = {
'mercury' : 500,    
'venus'   : 340,    # casa fix, was 367	    # n.a.
'mars'    : 195,    # casa fix, about same, # was 207
'jupiter' : 151,    # casa fix, was 173.5,  # was 172
'saturn'  : 146,    # no casa fix yet,      # was 149
'uranus'  : 130,    # casa fix, was 120,    # was 136
'neptune' : 120,    # casa fix, was 142,    # was 127
'pluto'   : 100,
'moon'	  : 150,	# an arbitrary number
'sun'	  : 6000	# an arbitrary number
}



def planetflux(inpbody, size, fcghz = 94., fchghz = None, sptype = 'rj'):
	# calculates the black body flux density 
	# given the brightness temperaute and size of the planet body
	# size = angular size of the planet in arcsec
	# fchghz if given, is a np.array listing frequencies of channels (1D or 2D)
	# fcghz = central frequency in GHz, flux will be calculated at this frequency 
	# if fchghz is not given
	# otherwise, avg flux calculated at each fchghz will be returned
	# flux will also be returned, which has the same dimension as fchghz 

        # sptype switches the flux returned (either 'rj' or 'bb')
        

        body = solbody(inpbody)
	Tb = Tdisc.get(body.lower(), -999)
	if (Tb == -999):
		print 'error: undefined brightness temperature for %s' % body.lower()
		sys.exit()

	diam = size / 3600. / 180. * np.pi
	omega = np.pi / 4. * diam**2

	fchghz = fchghz if fchghz else np.array([fcghz])

	s = fchghz.shape
	flat = []
	for f in fchghz.flat:
		nu = f * 1.e9
		#x  = h.value * nu / (k_B.value * Tb)
		#rj = 2. * k_B.value * Tb * nu**2 / c.value**2
		x  = h * nu / (k_B * Tb)
		rj = 2. * k_B * Tb * nu**2 / c**2   # unit: W/Hz/str
		rj *= omega * 1.e26                 # unit: Jy
		bb = rj * x / (np.exp(x) - 1.)
                if (sptype == 'bb'):
                    flat.append(bb)
                elif (sptype == 'rj'):
                    flat.append(rj)
                else:
                    print 'error: invalid spec. type.'
                    return None

	flux = np.array(flat).reshape(s)
	avgflux = np.mean(flux)

	return avgflux, flux

def solbody(body):
	## canonicalize the body name
	if   (body.lower() in 'jupiter'):
	    name = 'jupiter'
	elif (body.lower() in 'saturn' ):
	    name = 'saturn'
	elif (body.lower() in 'mars'   ):
	    name = 'mars'
	elif (body.lower() in 'neptune'):
	    name = 'neptune'
	elif (body.lower() in 'uranus'):
	    name = 'uranus'
	elif (body.lower() in 'venus'  ):
	    name = 'venus'
	elif (body.lower() in 'pluto'  ):
	    name = 'pluto'
	elif (body.lower() in 'mercury'):
            name = 'mercury'
	elif (body.lower() in 'moon'   ):
            name = 'moon'
	elif (body.lower() in 'sun'    ):
            name = 'sun'
	else:
	    print 'unknown PLANET =', body
	    sys.exit()

        return name

 
