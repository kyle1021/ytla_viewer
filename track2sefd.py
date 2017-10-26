#!/usr/bin/env python
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import sys
from loadh5 import *
from subprocess import call



#-- defaults --
inp	= sys.argv[0:]
pg	= inp.pop(0)
na      = 7
nb      = na * (na - 1) / 2
#tint    = 0.678                 # integration time used for SEFD calculation
bw      = 1.6 * (720./1024.)    # bandwidth used for SEFD calculation
chlim	= [20, 740]



#-- usage --
usage = """
syntax
    %s <oneh5> <sch_timing> <planet_flux> <tint>

    where 
	<oneh5>		the correlator data
	<sch_timing>	the timing of each patch
        <planet_flux>   the source flux in Jy (for SEFD calculation)
        <tint>          integration time per data point

NOTE:
    if some antenna is not working, it can be flagged in the config file 'ant_flag.config'
    put a single row of 1 (n_ant elements) if all antennas are working
    put a 0 for the antenna that is not working

""" % (pg)


#-- get input --
if (len(inp) < 4):
    print usage
    sys.exit()
else:
    foneh5= inp.pop(0)
    ftiming=inp.pop(0)
    fluxjy= float(inp.pop(0))
    tint  = float(inp.pop(0))


try:
    fd = open(foneh5, 'r')
    fd.close()
except IOError:
    print "error opening <shim_file> " + foneh5
    sys.exit()    
try:
    fd = open(ftiming, 'r')
    fd.close()
except IOError:
    print "error opening <shim_file> " + ftiming
    sys.exit()    



fconf = 'ant_flag.config'
if (os.path.isfile(fconf)):
    try:
	fd = open(fconf, 'r')
	fd.close()
	goodAnt = np.loadtxt(fconf)
    except IOError:
	print "error opening <flag_config>" + fconf
	print "(delete the file if it is not needed.)"
	sys.exit()
else:
    goodAnt = np.ones(na, dtype='int')




#-- load data --
(time, auto, cross) = ldoneh5(foneh5)
t = time - time[0]
print cross.shape
ca_cross = cross[:,:,chlim[0]:chlim[1],:].mean(axis=2)

ton, toff = np.loadtxt(ftiming, usecols=(0,1), unpack=True)
npatch = len(ton)
print 'npatch =', npatch

do_check = False
if (do_check):
    folder = foneh5 + '.traces'
    call(['mkdir', '-p', folder])
    for s in range(2):
	if (s == 0):
	    sb = 'lsb'
	else:
	    sb = 'usb'
	b = -1
	for ai in range(na-1):
	    for aj in range(ai+1, na):
		b += 1
		bl = '%d%d' % (ai, aj)
		print bl
		fout = '%s/bl%s.%s_time' % (folder, bl, sb)
		with open(fout, 'w') as f:
		    for i in range(len(t)):
			print >> f, '%.3f   %.6e' % (t[i], np.abs(ca_cross[s, b, i]))
		    



for s in range(2):
    if (s==0):
	sb = 'lsb'
    else:
	sb = 'usb'


    #-- prepare plots
    fig, subs = plt.subplots(2,1,sharex=True,sharey=False,figsize=(6,8))

    ## the bottom panel
    w = np.logical_and(t>=ton[1], t<=toff[npatch-2])
    tc = (ton[1] + toff[npatch-2]) / 2.

    for b in range(21):
	subs[1].plot(t[w], np.abs(ca_cross[s,b,w]))
    subs[1].set_xlabel('time (sec)')
    subs[1].set_ylabel('bl. amplitude')

    #-- derive noise --
    # first patch + last patch
    print 'patch  0:', ton[0], toff[0]
    w1 = np.logical_and(t>=ton[0], t<=toff[0])
    print '  num:', np.count_nonzero(w1)
    print 'patch -1:', ton[-1], toff[-1]
    w2 = np.logical_and(t>=ton[-1], t<=toff[-1])
    print '  num:', np.count_nonzero(w2)
    w  = np.logical_or(w1, w2)
    print 'both:'
    print '  num:', np.count_nonzero(w)

    rmsr = ca_cross[s:s+1,:,w].real.std(axis=(0,2))
    rmsi = ca_cross[s:s+1,:,w].imag.std(axis=(0,2))
    #print 'for ', sb
    #print 'rms for real part:', rmsr
    #print 'rms for imag part:', rmsi

    ## rms method 1
    rms1 = (rmsr + rmsi) / 2.
    #print 'method 1:'
    #print 'rms', rms1

    ## rms method 2
    rms2 = np.abs(ca_cross[s:s+1,:,w]).std(axis=(0,2))

    #print 'method 2:'
    #print 'rms', rms2

    print 'method 2 selected'
    rms = rms2

    #-- process --
    call(['mkdir', '-p', 'snr'])


    flog = '%s.%s.snr' % (foneh5, sb)
    log = open(flog, 'w')
    print >> log, '#t, SEFD(Jy:' + ' ant%d' * na % tuple(range(na)) + ')'

    for p in range(1, npatch-1):	# exclude first and last patch (noise)
    #for p in range(1,2):	# exclude first and last patch (noise)
	print 'patch ', p

	out = open('snr/result.patch_%02d' % p, 'w')

	w = np.logical_and(t>=ton[p], t<=toff[p])
	avga = np.abs(ca_cross[s:s+1, :, w]).mean(axis=(0,2))
	#print 'avg_ampld', avga
	peak = avga / rms	# 21 baselines (for 7-element)
	#print 'normalized', peak

	b = -1
	for ai in range(na-1):
	    for aj in range(ai+1, na):
		b += 1
		if (goodAnt[ai] and goodAnt[aj]):
		    pass
		else:
		    peak[b] = 1.e-30    # an arbitrarily small positive number

	#print "adjusted peak = ", peak
	print >> out, "peak power (corrected for misalignment attenuation) <-- per baseline"
	print >> out, peak
	print >> out, ""

	D = np.zeros(len(peak))
	D = np.log(peak)
	print >> out, "Data = log(power) <-- per baseline"
	print >> out, D
	print >> out, ""

	# we will solve A . X = D, given A and D
	# that is: X = Ainv * D
	# where Ainv comes from the pseudo-inverse np.linalg.pinv()

	## here the equations are
	## log(Pi) + log(Pj) = log(Pij)

	sh = (nb, na)
	A = np.zeros(sh)
	b = -1
	for i in range(na-1):
	    for j in range(i+1, na):
		b += 1
		#print i, j, b
		if (goodAnt[i] and goodAnt[j]):
		    A[b][i] = 0.5
		    A[b][j] = 0.5
		else:
		    A[b][i] = 0.
		    A[b][j] = 0.
		    D[b] = 0.


	print >> out, "solve X in (A dot X = D)\n"
	print >> out, "matrix A ="
	print >> out, A


	Ainv = np.linalg.pinv(A, rcond=1e-6)
	print >> out, "\ninverse matrix Ainv ="
	print >> out, Ainv

	print >> out, "\nunity test: Ainv dot A"
	print >> out, np.dot(Ainv, A)

	# X = log(P)
	X = np.dot(Ainv, D)
	R = D - np.dot(A, X)
	print >> out, "\nX = Ainv dot D"
	print >> out, X
	print >> out, "\nresidual R = D - A dot X"
	print >> out, R

	P = np.exp(X)
	print "antenna power: ", P
	print >> out, "\nantenna power P = exp(X)"
	print >> out, P

	SEFD = np.sqrt(2. * bw * 1.e9 * tint) * fluxjy / P
	for i in range(na):
	    if (not goodAnt[i]):
		SEFD[i] = 0.
	print "SEFD (Jy): ", '%.3e  '*na % tuple(SEFD)
	print >> out, "\nSEFD (Jy)"
	#print >> out, SEFD
	print >> out, '%.3e  '*na % tuple(SEFD)
	#out.write(str(SEFD))
	#print >> out, ''

	out.close()

	print >> log, '%.1f' % ((ton[p]+toff[p])/2.), '%.3e  '*na % tuple(SEFD)

    log.close()

    allsefd = np.loadtxt(flog, unpack=True)
    ang = (allsefd[0]-tc)*0.25
    for a in range(na):
	col = a+1
	subs[0].plot(allsefd[0], allsefd[col], label='ant%d, min=%.0f' % (a,allsefd[col].min()/1000.))

    subs[0].set_ylabel('SEFD (Jy)')
    subs[0].legend()
    subs[0].set_ylim([0,1.5e7])
    fig.suptitle('%s, %s' % (foneh5, sb))
    fig.savefig('%s.png' % flog)
    plt.close(fig)





