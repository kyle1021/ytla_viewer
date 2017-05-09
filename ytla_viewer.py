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
from subprocess import call

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
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ampax = self.fig.add_subplot(211)
        self.phaax = self.fig.add_subplot(212)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyInteractCanvas(MyMplCanvas):
    """Canvas to plot loaded data"""

    def clear(self):
	self.ampax.cla()
	self.phaax.cla()


    def add_trace(self, panel, x, y, **kwargs):
	if (panel == 'amp'):
	    ax = self.ampax
	elif (panel == 'pha'):
	    ax = self.phaax

	ax.plot(x, y, **kwargs)
	ax.legend()
	self.draw()


    def update_info(self, panel, **kwargs):
	if (panel == 'amp'):
	    ax = self.ampax
	elif (panel == 'pha'):
	    ax = self.phaax

	title = kwargs.get('title', '')
	if (title):
	    self.fig.suptitle(title)

	xlabel = kwargs.get('xlabel', '')
	if (xlabel):
	    ax.set_xlabel(xlabel)

	ylabel = kwargs.get('ylabel', '')
	if (ylabel):
	    ax.set_ylabel(ylabel)

	logY = kwargs.get('logY', 'keep')
	if (logY=='on'):
	    ax.set_yscale('log')
	elif (logY=='off'):
	    ax.set_yscale('linear')
	elif (logY=='keep'):
	    pass

	yLim = kwargs.get('yLim', [])
	if (len(yLim) == 2):
	    ymin, ymax = yLim
	    ax.set_ylim(ymin, ymax)
	else:
	    ax.set_ylim(auto=True)

	self.draw()


    def savefig(self, fname):
	self.fig.savefig(fname)



class ApplicationWindow(QtWidgets.QMainWindow):

    def __init__(self, fname='', bindir=''):
        QtWidgets.QMainWindow.__init__(self)

	self.fname = fname
	self.bindir = bindir

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
	self.calTab(self.tab2)
	self.convertTab(self.tab3)
	#self.placeHolder(self.tab3)
	

	# right pane -- plots
	self.right.layout = QtWidgets.QGridLayout(self.right)
	#self.ampplot = MyInteractCanvas(self.right, width=6, height=4, dpi=100)
	#self.phaplot = MyInteractCanvas(self.right, width=6, height=4, dpi=100)
	self.plot = MyInteractCanvas(self.right, width=6, height=8, dpi=100)
	#self.right.layout.addWidget(self.ampplot, 0, 0)
	#self.right.layout.addWidget(self.phaplot, 1, 0)
	self.right.layout.addWidget(self.plot, 0, 0, 3, 1)

	self.right.saveBtn = QtWidgets.QPushButton('Save fig ...', self.right)
	self.right.layout.addWidget(self.right.saveBtn, 0, 1)
	self.right.saveBtn.clicked.connect(self.savefig)

	# plotting options -- amp
	self.ampopt = QtWidgets.QFrame(self.right)
	self.ampopt.setFrameShape(1)
	self.ampopt.setFrameShadow(0)
	self.ampopt.setLineWidth(1)
	self.right.layout.addWidget(self.ampopt, 1, 1)
	self.ampopt.layout = QtWidgets.QVBoxLayout(self.ampopt)
	self.ampopt.btn1 = QtWidgets.QPushButton('Update', self.ampopt)
	self.ampopt.btn1.clicked.connect(self.update_ampplot)
	self.ampopt.layout.addWidget(self.ampopt.btn1, alignment=QtCore.Qt.AlignLeft)
	self.ampopt.logY = QtWidgets.QCheckBox('log-Y', self.ampopt)
	self.ampopt.logY.setChecked(False)
	self.ampopt.layout.addWidget(self.ampopt.logY, alignment=QtCore.Qt.AlignLeft)
	self.ampopt.Yscalelayout = QtWidgets.QGridLayout()
	self.ampopt.layout.addLayout(self.ampopt.Yscalelayout)
	self.ampopt.lab1 = QtWidgets.QLabel('Y-range:')
	self.ampopt.Yscalelayout.addWidget(self.ampopt.lab1, 0, 0)
	self.ampopt.BGYscale = QtWidgets.QButtonGroup(self.ampopt)
	self.ampopt.radAuto = QtWidgets.QRadioButton('Auto')
	self.ampopt.BGYscale.addButton(self.ampopt.radAuto)
	self.ampopt.BGYscale.setId(self.ampopt.radAuto, 0)
	self.ampopt.Yscalelayout.addWidget(self.ampopt.radAuto, 1, 0)
	self.ampopt.radFixed = QtWidgets.QRadioButton('Fixed')
	self.ampopt.BGYscale.addButton(self.ampopt.radFixed)
	self.ampopt.BGYscale.setId(self.ampopt.radFixed, 1)
	self.ampopt.Yscalelayout.addWidget(self.ampopt.radFixed, 2, 0)
	self.ampopt.radAuto.setChecked(True)
	self.ampopt.lab2 = QtWidgets.QLabel('min.')
	self.ampopt.lab3 = QtWidgets.QLabel('max.')
	self.ampopt.Yscalelayout.addWidget(self.ampopt.lab2, 3, 0, alignment=QtCore.Qt.AlignRight)
	self.ampopt.Yscalelayout.addWidget(self.ampopt.lab3, 4, 0, alignment=QtCore.Qt.AlignRight)
	self.ampopt.YminLE = QtWidgets.QLineEdit(self.ampopt)
	self.ampopt.YmaxLE = QtWidgets.QLineEdit(self.ampopt)
	self.ampopt.Yscalelayout.addWidget(self.ampopt.YminLE, 3, 1)
	self.ampopt.Yscalelayout.addWidget(self.ampopt.YmaxLE, 4, 1)
	
	self.ampopt.layout.addStretch(1)

	# plotting options -- pha
	self.phaopt = QtWidgets.QFrame(self.right)
	self.phaopt.setFrameShape(1)
	self.phaopt.setFrameShadow(0)
	self.phaopt.setLineWidth(1)
	self.right.layout.addWidget(self.phaopt, 2, 1)
	self.phaopt.layout = QtWidgets.QVBoxLayout(self.phaopt)
	self.phaopt.btn1 = QtWidgets.QPushButton('Update', self.phaopt)
	self.phaopt.btn1.clicked.connect(self.update_phaplot)
	self.phaopt.layout.addWidget(self.phaopt.btn1, alignment=QtCore.Qt.AlignLeft)
	self.phaopt.Yscalelayout = QtWidgets.QGridLayout()
	self.phaopt.layout.addLayout(self.phaopt.Yscalelayout)
	self.phaopt.lab1 = QtWidgets.QLabel('Y-range:')
	self.phaopt.Yscalelayout.addWidget(self.phaopt.lab1, 0, 0)
	self.phaopt.BGYscale = QtWidgets.QButtonGroup(self.phaopt)
	self.phaopt.radAuto = QtWidgets.QRadioButton('Auto')
	self.phaopt.BGYscale.addButton(self.phaopt.radAuto)
	self.phaopt.BGYscale.setId(self.phaopt.radAuto, 0)
	self.phaopt.Yscalelayout.addWidget(self.phaopt.radAuto, 1, 0)
	self.phaopt.radFixed = QtWidgets.QRadioButton('Fixed')
	self.phaopt.BGYscale.addButton(self.phaopt.radFixed)
	self.phaopt.BGYscale.setId(self.phaopt.radFixed, 1)
	self.phaopt.Yscalelayout.addWidget(self.phaopt.radFixed, 2, 0)
	self.phaopt.radFixed.setChecked(True)
	self.phaopt.lab2 = QtWidgets.QLabel('min.')
	self.phaopt.lab3 = QtWidgets.QLabel('max.')
	self.phaopt.Yscalelayout.addWidget(self.phaopt.lab2, 3, 0, alignment=QtCore.Qt.AlignRight)
	self.phaopt.Yscalelayout.addWidget(self.phaopt.lab3, 4, 0, alignment=QtCore.Qt.AlignRight)
	self.phaopt.YminLE = QtWidgets.QLineEdit(self.phaopt)
	self.phaopt.YmaxLE = QtWidgets.QLineEdit(self.phaopt)
	self.phaopt.YminLE.setText('-3.5')
	self.phaopt.YmaxLE.setText('3.5')
	self.phaopt.Yscalelayout.addWidget(self.phaopt.YminLE, 3, 1)
	self.phaopt.Yscalelayout.addWidget(self.phaopt.YmaxLE, 4, 1)
	
	self.phaopt.layout.addStretch(1)

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
	


    def convertTab(self, tab):
	# whole tab
	tab.layout = QtWidgets.QVBoxLayout(tab)


	# timestamp file
	tab.tsBox = QtWidgets.QGroupBox('Timestamp file', tab)
	tab.layout.addWidget(tab.tsBox)

	tab.tsBox.layout = QtWidgets.QGridLayout(tab.tsBox)
	btn1 = QtWidgets.QPushButton('Choose file ...', tab.tsBox)
	btn1.clicked.connect(self.openTfile)
	tab.tsBox.layout.addWidget(btn1, 0, 0)

	lab1 = QtWidgets.QLabel('-OR- Enter File')
	tab.tsBox.layout.addWidget(lab1, 0, 1)

	self.tsLE = QtWidgets.QLineEdit(tab.tsBox)
	self.tsLE.editingFinished.connect(self.getTfile)
	tab.tsBox.layout.addWidget(self.tsLE, 0, 2)

	lab2 = QtWidgets.QLabel('Num of Antenna:', tab.tsBox)
	tab.tsBox.layout.addWidget(lab2, 1, 0)
	self.naLE = QtWidgets.QLineEdit(tab.tsBox)
	self.naLE.setText(str(self.na))
	self.naLE.editingFinished.connect(self.update_na)
	tab.tsBox.layout.addWidget(self.naLE, 1, 1)

	btn2 = QtWidgets.QPushButton('Convert', tab.tsBox)
	btn2.clicked.connect(self.convert)
	tab.tsBox.layout.addWidget(btn2, 2, 0)


	# empty below
	tab.layout.addStretch(1)


    def update_na(self):
	try:
	    na = self.naLE.text()
	    self.na = na
	except ValueError:
	    pass


    def openTfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose File', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.tsLE.setText(rpath)
	    self.tsname = rpath

	
    def getTfile(self):
	try:
	    fname = self.tsLE.text()
	except ValueError:
	    fname = ''
	self.tsname = fname


    def convert(self):
	if (os.path.isfile(self.tsname)):
	    pass
	else:
	    print 'error finding timestamp file:', self.tsname
	    return 1

	rawname = self.tsname.rstrip('.timestamp') + '.raw.oneh5'
	print 'output to ', rawname

	time, auto, cross = ldcorr(self.tsname, self.na)
	print 'reading done.'

	wtoneh5(rawname, time, auto, cross)
	print 'writing done.'
	


    def calTab(self, tab):
	# whole tab
	tab.layout = QtWidgets.QVBoxLayout(tab)


	# raw data
	tab.rawBox = QtWidgets.QGroupBox('Source File', tab)
	tab.layout.addWidget(tab.rawBox)	
	tab.rawBox.layout = QtWidgets.QVBoxLayout(tab.rawBox)

	tab.RFilelayout = QtWidgets.QHBoxLayout()
	tab.rawBox.layout.addLayout(tab.RFilelayout)
	btn1 = QtWidgets.QPushButton('Choose file ...', tab.rawBox)
	btn1.clicked.connect(self.openRfile)
	tab.RFilelayout.addWidget(btn1, alignment=QtCore.Qt.AlignLeft)
	tab.rawBox.lab1 = QtWidgets.QLabel('-Or- Enter File')
	tab.RFilelayout.addWidget(tab.rawBox.lab1)
	self.rawLE = QtWidgets.QLineEdit(tab.rawBox)
	self.rawLE.editingFinished.connect(self.getRfile)
	#self.rawLE.setText(self.rawname)
	tab.RFilelayout.addWidget(self.rawLE)

	
	# cal data
	tab.calBox = QtWidgets.QGroupBox('Calibrator File', tab)
	tab.layout.addWidget(tab.calBox)	
	tab.calBox.layout = QtWidgets.QVBoxLayout(tab.calBox)

	tab.CFilelayout = QtWidgets.QHBoxLayout()
	tab.calBox.layout.addLayout(tab.CFilelayout)
	btn3 = QtWidgets.QPushButton('Choose file ...', tab.calBox)
	btn3.clicked.connect(self.openCfile)
	tab.CFilelayout.addWidget(btn3, alignment=QtCore.Qt.AlignLeft)
	tab.calBox.lab1 = QtWidgets.QLabel('-Or- Enter File')
	tab.CFilelayout.addWidget(tab.calBox.lab1)
	self.calLE = QtWidgets.QLineEdit(tab.calBox)
	self.calLE.editingFinished.connect(self.getCfile)
	#self.calLE.setText(self.calname)
	tab.CFilelayout.addWidget(self.calLE)
	tab.calBox.note = QtWidgets.QLabel("Note: enter 'self' in the field above for self-calibration.")
	tab.calBox.layout.addWidget(tab.calBox.note)


	# option and calibrate
	tab.optBox = QtWidgets.QGroupBox('Options', tab)
	tab.layout.addWidget(tab.optBox)
	tab.optBox.layout = QtWidgets.QGridLayout(tab.optBox)

	tab.optBox.lab1 = QtWidgets.QLabel('Bandpass Cal.:')
	self.CBpcal = QtWidgets.QCheckBox('phase')
	self.CBgcal = QtWidgets.QCheckBox('gain')
	self.CBpcal.setChecked(True)
	tab.optBox.layout.addWidget(tab.optBox.lab1, 0, 0)
	tab.optBox.layout.addWidget(self.CBpcal, 0, 1)
	tab.optBox.layout.addWidget(self.CBgcal, 0, 2)

	btn5 = QtWidgets.QPushButton('Calibrate', tab.optBox)
	btn5.clicked.connect(self.calibrate)
	tab.optBox.layout.addWidget(btn5, 1, 0)



	# empty space below
	tab.layout.addStretch(1)



    def openRfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose File', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.rawLE.setText(rpath)
	    self.rawname = rpath


    def openCfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose File', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.calLE.setText(rpath)
	    self.calname = rpath


    def getRfile(self):
	try:
	    fname = self.rawLE.text()
	except ValueError:
	    fname = ''
	self.rawname = fname


    def getCfile(self):
	try:
	    fname = self.calLE.text()
	except ValueError:
	    fname = ''
	self.calname = fname


    def calibrate(self):
	if (os.path.isfile(self.rawname)):
	    pass
	else:
	    print 'error finding raw_file,', self.rawname
	    return 1

	if (os.path.isfile(self.calname) or self.calname == 'self'):
	    pass
	else:
	    print 'error finding cal_file,', self.calname
	    return 1

	calexe = '%s/calibrate_oneh5.py' % self.bindir
	cmd = [calexe, self.rawname, self.calname]

	if (self.CBpcal.isChecked()):
	    pass		# default is to do pcal
	else:
	    cmd.append('-pcal')	# this turns off pcal

	if (self.CBgcal.isChecked()):
	    cmd.append('-gcal')	# this turns on gcal
	else:
	    pass		# default is to not do gcal

	call(cmd)



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
	self.antj   = 1		    

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
	btn1 = QtWidgets.QPushButton('Choose file ...', tab.selectFile)
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
	tab.vsTime = QtWidgets.QFrame(tab.actionRow)
	tab.vsTime.setFrameShape(1)
	tab.vsTime.setLineWidth(1)
	tab.actionRow.layout.addWidget(tab.vsTime)
	tab.vsTime.layout = QtWidgets.QVBoxLayout(tab.vsTime)
	tab.vsChan = QtWidgets.QFrame(tab.actionRow)
	tab.vsChan.setFrameShape(1)
	tab.vsChan.setLineWidth(1)
	tab.actionRow.layout.addWidget(tab.vsChan)
	tab.vsChan.layout = QtWidgets.QVBoxLayout(tab.vsChan)
	tab.vsTime.lab1 = QtWidgets.QLabel('vs. Time')
	tab.vsTime.layout.addWidget(tab.vsTime.lab1)
	tab.vsTime.singleBtn = QtWidgets.QPushButton('Single Trace', tab.dataBox)
	tab.vsTime.singleBtn.clicked.connect(self.newplotvstime)
	tab.vsTime.layout.addWidget(tab.vsTime.singleBtn)
	tab.vsTime.addBtn = QtWidgets.QPushButton('Add Trace', tab.dataBox)
	tab.vsTime.addBtn.clicked.connect(self.plotvstime)
	tab.vsTime.layout.addWidget(tab.vsTime.addBtn)
	tab.vsChan.lab1 = QtWidgets.QLabel('vs. Chan')
	tab.vsChan.layout.addWidget(tab.vsChan.lab1)
	tab.vsChan.singleBtn = QtWidgets.QPushButton('Single Trace', tab.dataBox)
	tab.vsChan.singleBtn.clicked.connect(self.newplotvschan)
	tab.vsChan.layout.addWidget(tab.vsChan.singleBtn)
	tab.vsChan.addBtn = QtWidgets.QPushButton('Add Trace', tab.dataBox)
	tab.vsChan.addBtn.clicked.connect(self.plotvschan)
	tab.vsChan.layout.addWidget(tab.vsChan.addBtn)

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
	tab.binRow.lab1 = QtWidgets.QLabel('Binning: ')
	tab.binRow.layout.addWidget(tab.binRow.lab1)
	tab.binRow.lab2 = QtWidgets.QLabel('chan_bin')
	tab.binRow.layout.addWidget(tab.binRow.lab2)
	self.chbinLE = QtWidgets.QLineEdit(tab.binRow)
	self.chbinLE.setText('%d' % self.chbin)
	self.chbinLE.editingFinished.connect(self.verifyBin)
	tab.binRow.layout.addWidget(self.chbinLE)
	tab.binRow.lab3 = QtWidgets.QLabel('time_bin')
	tab.binRow.layout.addWidget(tab.binRow.lab3)
	self.tbinLE = QtWidgets.QLineEdit(tab.binRow)
	self.tbinLE.setText('%d' % self.tbin)
	self.tbinLE.editingFinished.connect(self.verifyBin)
	tab.binRow.layout.addWidget(self.tbinLE)



	# empty space below
	tab.layout.addStretch(1)




    def openfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose File', '.')

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

	try:
	    self.tlim[0] = float(self.tlimLE[0].text())
	    self.tlim[1] = float(self.tlimLE[1].text())
	except ValueError:
	    self.statusBar().showMessage('Data not loaded. Abort!', 2000)
	    print 'data is Not loaded'
	    return 1
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


	self.selectBL = '%d-%d' % (self.anti, self.antj)

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


    def update_ampplot(self):
	logY = self.ampopt.logY.isChecked()
	if (logY):
	    self.plot.update_info('amp', logY='on')
	else:
	    self.plot.update_info('amp', logY='off')

	yScale = self.ampopt.BGYscale.checkedId()
	if (yScale == 0):   # auto
	    self.plot.update_info('amp', yLim=[])
	elif (yScale == 1): # fixed
	    try:
		ymin = float(self.ampopt.YminLE.text())
		ymax = float(self.ampopt.YmaxLE.text())
		self.plot.update_info('amp', yLim=[ymin, ymax])
	    except ValueError:
		print 'fixed range; Y-range not set?'
		self.statusBar().showMessage('fixed range; Y-range not set?', 2000)
		return None


    def update_phaplot(self):
	yScale = self.phaopt.BGYscale.checkedId()
	if (yScale == 0):   # auto
	    self.plot.update_info('pha', yLim=[])
	elif (yScale == 1): # fixed
	    try:
		ymin = float(self.phaopt.YminLE.text())
		ymax = float(self.phaopt.YmaxLE.text())
		self.plot.update_info('pha', yLim=[ymin, ymax])
	    except ValueError:
		print 'fixed range; Y-range not set?'
		self.statusBar().showMessage('fixed range; Y-range not set?', 2000)
		return None


    def newplotvstime(self):
	self.plot.clear()
	self.plotvstime()
	self.plot.update_info('amp', title=self.fname, xlabel='Time (sec)', ylabel='Amplitude')
	self.plot.update_info('pha', title=self.fname, xlabel='Time (sec)', ylabel='Phase (rad)')


    def plotvstime(self):
	if (self.dataRebin() == 0):
	    pass
	else:
	    self.statusBar().showMessage('Data re-bin error. Abort!', 2000)
	    return None

	x = self.t1
	a = np.abs(self.plotData.mean(axis=0))
	p = np.angle(self.plotData.mean(axis=0))

	label = 'BL%s, SB%d' % (self.selectBL, self.sb)
	self.plot.add_trace('amp', x, a, label=label)
	self.plot.add_trace('pha', x, p, label=label)



    def newplotvschan(self):
	self.plot.clear()
	self.plotvschan()
	self.plot.update_info('amp', title=self.fname, xlabel='Channel (ch)', ylabel='Amplitude')
	self.plot.update_info('pha', title=self.fname, xlabel='Channel (ch)', ylabel='Phase (rad)')


    def plotvschan(self):
	if (self.dataRebin() == 0):
	    pass
	else:
	    self.statusBar().showMessage('Data re-bin error. Abort!', 2000)
	    return None

	x = self.ch1
	a = np.abs(self.plotData.mean(axis=1))
	p = np.angle(self.plotData.mean(axis=1))

	label = 'BL%s, SB%d' % (self.selectBL, self.sb)
	self.plot.add_trace('amp', x, a, label=label)
	self.plot.add_trace('pha', x, p, label=label)


    def savefig(self):
	fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Filename', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.plot.savefig(rpath)



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

    pg = inp.pop(0)
    progname = os.path.basename(pg)
    bindir   = os.path.dirname(pg)

    fname = ''
    while (inp):
	f = inp.pop(0)
	if os.path.isfile(f):
	    fname = f

    aw = ApplicationWindow(fname=fname, bindir=bindir)
    aw.setWindowTitle("%s" % progname)
    aw.show()

    sys.exit(qApp.exec_())
    #qApp.exec_()


