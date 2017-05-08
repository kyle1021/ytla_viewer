#!/usr/bin/env python

# embedding_in_qt5.py --- Simple Qt5 application embedding matplotlib canvases
#
# Copyright (C) 2005 Florent Rougon
#               2006 Darren Dale
#               2015 Jens H Nielsen
#
# This file is an example program for matplotlib. It may be used and
# modified with no restriction; raw copies as well as modified versions
# may be distributed without limitation.


from __future__ import unicode_literals
import sys, os, os.path

import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from numpy import arange, sin, pi
from loadh5 import *





class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyInteractCanvas(MyMplCanvas):
    """Canvas to plot loaded data"""

    def update_figure(self, x, y):
	self.axes.cla()
	#print 'update_figure', x, y
	self.axes.plot(x, y)
	self.draw()



class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()


class ApplicationWindow(QtWidgets.QMainWindow):

    def __init__(self, fname=''):
        QtWidgets.QMainWindow.__init__(self)

	self.fname = fname

	self.initUI()



    def initUI(self):

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

	# menu bar
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)


	# main window widget
        self.main = QtWidgets.QWidget(self)
	self.main.layout = QtWidgets.QHBoxLayout(self.main)
	self.left  = QtWidgets.QTabWidget(self.main)
	self.main.layout.addWidget(self.left)
	self.right = QtWidgets.QWidget(self.main)
	self.main.layout.addWidget(self.right)


	# left pane -- applications, tabbed
	self.tab1 = QtWidgets.QWidget()
	self.tab2 = QtWidgets.QWidget()
	self.tab3 = QtWidgets.QWidget()

	self.left.addTab(self.tab1, 'Plot Data')
	self.left.addTab(self.tab2, 'BandPass Cal.')
	self.left.addTab(self.tab3, 'Data Conversion')

	#self.placeHolder(self.tab1)
	self.plotTab(self.tab1)
	self.placeHolder(self.tab2)
	self.placeHolder(self.tab3)
	

	# right pane -- plots
	self.right.layout = QtWidgets.QVBoxLayout(self.right)
	self.ampplot = MyInteractCanvas(self.right, width=6, height=4, dpi=100)
	self.phaplot = MyInteractCanvas(self.right, width=6, height=4, dpi=100)
	self.right.layout.addWidget(self.ampplot)
	self.right.layout.addWidget(self.phaplot)


	# central
        self.main.setFocus()
        self.setCentralWidget(self.main)
	self.move(50,50)
        #self.statusBar().showMessage("All hail matplotlib!", 2000)



    def placeHolder(self, tab):
	wip  = QtWidgets.QLabel('under construction.')
	tab.layout = QtWidgets.QVBoxLayout(tab)
	tab.layout.addWidget(wip)
	tab.layout.addStretch(1)
	



    def plotTab(self, tab):
	'''tab (the input) is a QWidget intended for loading data and controlling the plots'''

	# default values
	self.nsb    = 2		    # will update after data is loaded
	self.na	    = 4		    # will update after data is loaded
	self.ma	    = 4		    # max number of antennas (for layout)
	self.nch    = 1024
	self.npt    = 0		    # data length (points), will be updated
	self.bw	    = 1.6	    # bandwidth, GHz

	self.sb	    = 0		    # 0=LSB, 1=USB
	self.chlim  = [20, 760]	    # channel range
	self.tlim   = [0, 0]	    # will update after data is loaded
	self.anti   = 0		    # plotting anti X antj
	self.antj   = 0		    

	self.tbin   = 1		    # default binning
	self.chbin  = 1



	# whole tab
	tab.layout = QtWidgets.QVBoxLayout(tab)


	# file loading box
	tab.fileBox = QtWidgets.QGroupBox('File Loading', tab)
	tab.layout.addWidget(tab.fileBox)	
	tab.fileBox.layout = QtWidgets.QVBoxLayout(tab.fileBox)

	tab.selectFile = QtWidgets.QWidget(tab.fileBox)
	tab.fileBox.layout.addWidget(tab.selectFile)
	tab.selectFile.layout = QtWidgets.QHBoxLayout(tab.selectFile)
	btn1 = QtWidgets.QPushButton('Open file ...', tab.selectFile)
	btn1.clicked.connect(self.openfile)
	tab.selectFile.layout.addWidget(btn1, alignment=QtCore.Qt.AlignLeft)
	tab.selectFile.lab1 = QtWidgets.QLabel('-Or- Enter File')
	tab.selectFile.layout.addWidget(tab.selectFile.lab1)
	self.fileLE = QtWidgets.QLineEdit(tab.selectFile)
	self.fileLE.setText(self.fname)
	tab.selectFile.layout.addWidget(self.fileLE)

	btn2 = QtWidgets.QPushButton('Load', tab.fileBox)
	btn2.clicked.connect(self.loadfile)
	tab.fileBox.layout.addWidget(btn2)

	tab.dataProp = QtWidgets.QWidget(tab.fileBox)
	tab.fileBox.layout.addWidget(tab.dataProp)
	tab.dataProp.layout = QtWidgets.QGridLayout(tab.dataProp)
	tab.dataProp.lab1 = QtWidgets.QLabel('File loaded:', tab.dataProp)
	self.fileLab = QtWidgets.QLabel('', tab.dataProp)
	tab.dataProp.lab2 = QtWidgets.QLabel('Nsb, Na, Nch, Npt = ', tab.dataProp)
	self.shapeLab = QtWidgets.QLabel('', tab.dataProp)
	tab.dataProp.layout.addWidget(tab.dataProp.lab1, 0, 0)
	tab.dataProp.layout.addWidget(self.fileLab, 0, 1)
	tab.dataProp.layout.addWidget(tab.dataProp.lab2, 1, 0)
	tab.dataProp.layout.addWidget(self.shapeLab, 1, 1)



	# data selection box
	tab.dataBox = QtWidgets.QGroupBox('Data Selection', tab)
	tab.layout.addWidget(tab.dataBox)
	tab.dataBox.layout = QtWidgets.QVBoxLayout(tab.dataBox)

	tab.actionRow = QtWidgets.QWidget(tab.dataBox)
	tab.dataBox.layout.addWidget(tab.actionRow)
	tab.actionRow.layout = QtWidgets.QHBoxLayout(tab.actionRow)
	btn3 = QtWidgets.QPushButton('Plot vs. Time', tab.dataBox)
	btn3.clicked.connect(self.plotvstime)
	tab.actionRow.layout.addWidget(btn3)
	btn4 = QtWidgets.QPushButton('Plot vs. Chan', tab.dataBox)
	btn4.clicked.connect(self.plotvschan)
	tab.actionRow.layout.addWidget(btn4)

	tab.selectSB = QtWidgets.QWidget(tab.dataBox)
	tab.dataBox.layout.addWidget(tab.selectSB)
	tab.selectSB.layout = QtWidgets.QHBoxLayout(tab.selectSB)
	tab.selectSB.lab1 = QtWidgets.QLabel('Sidband:', tab.selectSB)
	tab.selectSB.layout.addWidget(tab.selectSB.lab1)
	self.BGSB = QtWidgets.QButtonGroup(tab.selectSB)
	tab.radSB = []
	tab.radSB.append( QtWidgets.QRadioButton('LSB', tab.selectSB) )
	tab.radSB.append( QtWidgets.QRadioButton('USB', tab.selectSB) )
	tab.selectSB.layout.addWidget(tab.radSB[0])
	tab.selectSB.layout.addWidget(tab.radSB[1])
	self.BGSB.addButton(tab.radSB[0])
	self.BGSB.addButton(tab.radSB[1])
	self.BGSB.setId(tab.radSB[0], 0)
	self.BGSB.setId(tab.radSB[1], 1)
	tab.radSB[self.sb].setChecked(True)
	self.BGSB.buttonClicked.connect(self.updateSB)
	tab.selectSB.layout.addStretch(1)

	tab.selectANTi = QtWidgets.QWidget(tab.dataBox)
	tab.dataBox.layout.addWidget(tab.selectANTi)
	tab.selectANTi.layout = QtWidgets.QHBoxLayout(tab.selectANTi)
	tab.selectANTi.lab1 = QtWidgets.QLabel('Ant-i')
	tab.selectANTi.layout.addWidget(tab.selectANTi.lab1)
	self.BGANTi = QtWidgets.QButtonGroup(tab.selectANTi)
	tab.radANTi = []
	for i in range(self.ma):
	    tab.radANTi.append( QtWidgets.QRadioButton('%d' % i, tab.selectANTi) )
	    tab.selectANTi.layout.addWidget(tab.radANTi[i])
	    self.BGANTi.addButton(tab.radANTi[i])
	    self.BGANTi.setId(tab.radANTi[i], i)
	tab.radANTi[self.anti].setChecked(True)
	tab.selectANTi.layout.addStretch(1)

	tab.selectANTj = QtWidgets.QWidget(tab.dataBox)
	tab.dataBox.layout.addWidget(tab.selectANTj)
	tab.selectANTj.layout = QtWidgets.QHBoxLayout(tab.selectANTj)
	tab.selectANTj.lab1 = QtWidgets.QLabel('Ant-j')
	tab.selectANTj.layout.addWidget(tab.selectANTj.lab1)
	self.BGANTj = QtWidgets.QButtonGroup(tab.selectANTj)
	tab.radANTj = []
	for j in range(self.ma):
	    tab.radANTj.append( QtWidgets.QRadioButton('%d' % j, tab.selectANTj) )
	    tab.selectANTj.layout.addWidget(tab.radANTj[j])
	    self.BGANTj.addButton(tab.radANTj[j])
	    self.BGANTj.setId(tab.radANTj[j], j)
	tab.radANTj[self.antj].setChecked(True)
	tab.selectANTj.layout.addStretch(1)



	# plot setup
	tab.plotBox = QtWidgets.QGroupBox('Plot setup', tab)
	tab.layout.addWidget(tab.plotBox)
	tab.plotBox.layout = QtWidgets.QVBoxLayout(tab.plotBox)

	tab.chanRow = QtWidgets.QWidget(tab.plotBox)
	tab.plotBox.layout.addWidget(tab.chanRow)
	tab.chanRow.layout = QtWidgets.QHBoxLayout(tab.chanRow)
	tab.chanRow.lab1 = QtWidgets.QLabel('Chan Range:')
	tab.chanRow.layout.addWidget(tab.chanRow.lab1)
	self.chlimLE = []
	self.chlimLE.append(QtWidgets.QLineEdit(tab.chanRow))
	self.chlimLE.append(QtWidgets.QLineEdit(tab.chanRow))
	tab.chanRow.layout.addWidget(self.chlimLE[0])
	tab.chanRow.layout.addWidget(self.chlimLE[1])
	self.chlimLE[0].setText('%d' % self.chlim[0])
	self.chlimLE[1].setText('%d' % self.chlim[1])
	tab.chanRow.lab2 = QtWidgets.QLabel('(ch)')
	tab.chanRow.layout.addWidget(tab.chanRow.lab2)

	tab.timeRow = QtWidgets.QWidget(tab.plotBox)
	tab.plotBox.layout.addWidget(tab.timeRow)
	tab.timeRow.layout = QtWidgets.QHBoxLayout(tab.timeRow)
	tab.timeRow.lab1 = QtWidgets.QLabel('Time Range:')
	tab.timeRow.layout.addWidget(tab.timeRow.lab1)
	self.tlimLE = []
	self.tlimLE.append(QtWidgets.QLineEdit(tab.timeRow))
	self.tlimLE.append(QtWidgets.QLineEdit(tab.timeRow))
	tab.timeRow.layout.addWidget(self.tlimLE[0])
	tab.timeRow.layout.addWidget(self.tlimLE[1])
	tab.timeRow.lab2 = QtWidgets.QLabel('(sec)')
	tab.timeRow.layout.addWidget(tab.timeRow.lab2)
	
	tab.binRow = QtWidgets.QWidget(tab.plotBox)
	tab.plotBox.layout.addWidget(tab.binRow)
	tab.binRow.layout = QtWidgets.QHBoxLayout(tab.binRow)
	tab.binRow.lab1 = QtWidgets.QLabel('Re-bin: ')
	tab.binRow.layout.addWidget(tab.binRow.lab1)
	tab.binRow.lab2 = QtWidgets.QLabel('chan-ch')
	tab.binRow.layout.addWidget(tab.binRow.lab2)
	self.chbinLE = QtWidgets.QLineEdit(tab.binRow)
	self.chbinLE.setText('%d' % self.chbin)
	self.chbinLE.editingFinished.connect(self.verifyBin)
	tab.binRow.layout.addWidget(self.chbinLE)
	tab.binRow.lab3 = QtWidgets.QLabel('time-pt')
	tab.binRow.layout.addWidget(tab.binRow.lab3)
	self.tbinLE = QtWidgets.QLineEdit(tab.binRow)
	self.tbinLE.setText('%d' % self.tbin)
	self.tbinLE.editingFinished.connect(self.verifyBin)
	tab.binRow.layout.addWidget(self.tbinLE)



	# empty space below
	tab.layout.addStretch(1)




    def openfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.fileLE.setText(rpath)
	    self.fileLab.setText(rpath)
	    self.fname = rpath


    def loadfile(self):
	fname = self.fileLE.text()
	if (self.fname):
	    pass
	elif (fname != ''):
	    self.fname = fname
	    self.fileLab.setText(fname)
	    
	if (self.fname):
	    if (self.fname.find('.oneh5') > -1):
		self.time, self.auto, self.cross = ldoneh5(self.fname)
	    elif (self.fname.find('.timestamp') > -1):
		self.time, self.auto, self.cross = ldcorr(self.fname, self.na)

	    self.nsb, self.na, self.nch, self.npt = self.auto.shape
	    self.shapeLab.setText(repr(self.auto.shape))
	    self.t0 = self.time - self.time[0]
	    self.ch0 = np.array(range(nch))
	    self.tlim = [self.t0[0], self.t0[-1]]
	    self.tlimLE[0].setText('%.3f' % self.tlim[0])
	    self.tlimLE[1].setText('%.3f' % self.tlim[1])
	    self.bl = np.zeros((self.na-1, self.na), dtype=int)	# anti: 0, na-2; antj = 1, na-1
	    b = 0
	    for i in range(self.na-1):
		for j in range(i+1, self.na):
		    self.bl[i, j] = b
		    b += 1

	else:
	    self.statusBar().showMessage("no file selected!", 2000)


    def updateSB(self):
	self.sb = self.BGSB.checkedId()
	print '(Usr) SB:', self.sb


    def verifyANT(self):
	anti = self.BGANTi.checkedId()
        antj = self.BGANTj.checkedId()
	if (anti <= antj):  # valid
	    self.anti = anti
	    self.antj = antj
	    return 0	# success
	else:
	    self.statusBar().showMessage('antenna selection error!', 2000)
	    return 1	# failed


    def verifyBin(self):
	try:
	    chbin = int(self.chbinLE.text())
	    tbin  = int(self.tbinLE.text())
	except ValueError:
	    self.statusBar().showMessage('invalid bin!!!', 2000)

	if (chbin >= 1 and tbin >=1):
	    self.chbin = chbin
	    self.tbin  = tbin
	    print '(Usr) chbin', chbin, 'tbin', tbin
	else:
	    self.statusBar().showMessage('bin out of range.', 2000)



    def dataRebin(self):
	if (self.verifyANT() == 0):
	    print 'passed ANT:', self.anti, self.antj
	    pass
	else:
	    return 1	# failed

	self.tlim[0] = float(self.tlimLE[0].text())
	self.tlim[1] = float(self.tlimLE[1].text())
	#print self.tlim, self.t0[0], self.t0[-1]
	if (self.tlim[0] >= self.t0[0] and self.tlim[1] <= self.t0[-1]+0.001 and self.tlim[0] < self.tlim[1]):
	    #print 'passed tlim:', self.tlim
	    pass
	else:
	    self.statusBar().showMessage('Time range error. Abort!', 2000)
	    return 1	# failed

	self.chlim[0] = float(self.chlimLE[0].text())
	self.chlim[1] = float(self.chlimLE[1].text())
	if (self.chlim[0] >= self.ch0[0] and self.chlim[1] <= self.ch0[-1] and self.chlim[0] < self.chlim[1]):
	    #print 'passed chlim:', self.chlim
	    pass
	else:
	    self.statusBar().showMessage('Chan range error. Abort!', 2000)
	    return 1	# failed


	if (self.anti == self.antj):	# auto
	    raw = self.auto[self.sb, self.anti]
	    print 'auto'
	else:				# cross
	    b = self.bl[self.anti, self.antj]
	    raw = self.cross[self.sb, b]
	    print 'cross, b =', b
	#print 'raw.shape', raw.shape

        (M0, M1) = raw.shape	# = (nch, npt)
	N0 = self.chbin
	N1 = self.tbin
	print 're-Bin:', N0, N1

	# binned data
	if (N0>1 or N1>1):	# re-bin
	    N0 = min(N0, M0)
	    N1 = min(N1, M1)
	    nbin0 = M0 // N0
	    nbin1 = M1 // N1
	    self.plotData = raw[:(nbin0 * N0), :(nbin1 * N1)].reshape(nbin0, N0, nbin1, N1).mean(axis=(1,3))
	    self.ch1 = self.ch0[:(nbin0 * N0)].reshape(nbin0, N0).mean(axis=1) 
	    self.t1  = self.t0[:(nbin1 * N1)].reshape(nbin1, N1).mean(axis=1) 
	else:			# raw-bin
	    self.plotData = raw
	    self.ch1 = self.ch0
	    self.t1  = self.t0

	# choose range
	#w0 = np.logical_and(self.ch1 > self.chlim[0], self.ch1 < self.chlim[1])
	#w1 = np.logical_and(self.t1 >= self.tlim[0], self.t1 <= self.tlim[1])
	## note: we can not use self.plotData[w0, w1] to select range.
	##       self.plotData[w0,:] or self.plotData[:,w1] would both be valid though
	(w00, w01) = np.abs(self.ch1 - self.chlim[0]).argmin(), np.abs(self.ch1 - self.chlim[1]).argmin()
	(w10, w11) = np.abs(self.t1 - self.tlim[0]).argmin(),   np.abs(self.t1 - self.tlim[1]).argmin()
	#print self.chlim, self.ch1
	#print self.tlim, self.t1
	#print 'ch range:', w00, w01
	#print 'pt range:', w10, w11
	self.plotData = self.plotData[w00:w01+1, w10:w11+1]
	self.ch1 = self.ch1[w00:w01+1]
	self.t1  = self.t1[w10:w11+1]
	

	#print 're-bin successful'
	return 0	# success


    def plotvstime(self):
	if (self.dataRebin() == 0):
	    pass
	else:
	    self.statusBar().showMessage('Data re-bin error. Abort!', 2000)
	    return None

	x = self.t1
	a = np.abs(self.plotData.mean(axis=0))
	p = np.angle(self.plotData.mean(axis=0))

	self.ampplot.update_figure(x, a)
	self.phaplot.update_figure(x, p)




    def plotvschan(self):
	if (self.dataRebin() == 0):
	    pass
	else:
	    self.statusBar().showMessage('Data re-bin error. Abort!', 2000)
	    return None

	x = self.ch1
	a = np.abs(self.plotData.mean(axis=1))
	p = np.angle(self.plotData.mean(axis=1))

	self.ampplot.update_figure(x, a)
	self.phaplot.update_figure(x, p)




    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About", """
This data viewer is intended for the 1k channel digital correlator of the AIM-CO project. It has three major functions: (1) plotting data, (2) bandpass calibration, and (3) data format conversion. -- Kyle Lin (May/2017)"""



                                )

if (__name__ == '__main__'):

    inp = sys.argv[0:]

    qApp = QtWidgets.QApplication(inp)

    progname = os.path.basename(inp.pop(0))

    fname = ''
    while (inp):
	f = inp.pop(0)
	if os.path.isfile(f):
	    fname = f

    aw = ApplicationWindow(fname=fname)
    aw.setWindowTitle("%s" % progname)
    aw.show()

    sys.exit(qApp.exec_())
    #qApp.exec_()


