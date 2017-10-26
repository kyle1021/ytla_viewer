#!/usr/bin/env python
# calculates the apparent (date) coordinates of planets
# for Saturn, also can calculate the ring inclination (earth_tilt)
# 2011/06/02

from ephem import *
import sys
from datetime import datetime
from pyplanet import *


## preparation
inp	= sys.argv[0:]
pg	= inp[0]
now	= datetime.utcnow()    # force UTC
time	= now  # default time
epoch	= '2000'


## user inputs
usage = "\nusage: %s PLANET [time [epoch]]\n\t[optional]:\n\ttime = 'now' or 'yyyy-mm-dd HH:MM:SS'\n\tepoch = '2000', '1950', or something\n" % pg

if (len(inp) < 2):
    print usage
    sys.exit()
elif (len(inp) >= 3):
    arg = inp[2]
    if (arg != 'now'):
	time = arg
    if (len(inp) >= 4):
	epoch = inp[3]

body  = inp[1]


## using the function
b = mloplanet(body, time, epoch)

#format = '%s %s  %s\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\n'
#line = format % (long, parts[0], seconds, acu_rar, acu_dcr, app_rar, app_dcr, float(sep))
print "\nCoordinates calculated for UTC:"
print time
print "\nAstrometric coordinates -- geocentric -- (epoch = '%s'):" % epoch
print b.a_ra, b.a_dec
print "\nApparent coordinates -- topocentric -- (MLO, epoch = date):"
print b.ra, b.dec
print "\nAngular diameter (arcsec):"
print b.size
if (body.lower() == 'saturn'):
    print "\nRing inclination (toward earth; southward > 0, northward < 0; deg):"
    print b.earth_tilt
print "\nTransit time:"
print b.transit_time
print ''
