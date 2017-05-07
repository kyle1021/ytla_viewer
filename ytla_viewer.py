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



progname = os.path.basename(sys.argv[0])
progversion = "0.1"


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




class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)


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

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

	self.initUI()



    def initUI(self):

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)


	# default values
	self.nsb    = 2		    # will update after data is loaded
	self.na	    = 4		    # will update after data is loaded
	ma	    = 4		    # max number of antennas (for layout)
	self.nch    = 1024
	self.npt    = 0		    # data length (points), will be updated

	self.sb	    = 0		    # 0=LSB, 1=USB
	self.chlim  = [5, 750]	    # channel range
	self.tlim   = [0, 0]	    # will update after data is loaded
	self.anti   = 0		    # plotting anti X antj
	self.antj   = 0		    

	self.tbin   = 1		    # default binning
	self.chbin  = 1



	# widgets
        self.main_widget = QtWidgets.QWidget(self)

        #rsc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        #rdc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
	self.ic = MyInteractCanvas(self.main_widget, width=5, height=4, dpi=100)

	self.fname = ''
	btn1 = QtWidgets.QPushButton('Open file ...', self.main_widget)
	btn1.clicked.connect(self.openfile)

	btn2 = QtWidgets.QPushButton('Load', self.main_widget)
	btn2.clicked.connect(self.loadfile)

	btn3 = QtWidgets.QPushButton('Plot', self.main_widget)
	btn3.clicked.connect(self.plotfile)


	self.le = QtWidgets.QLineEdit(self.main_widget)
	self.lab1 = QtWidgets.QLabel('Data loaded:', self.main_widget)
	self.lab2 = QtWidgets.QLabel('', self.main_widget)
	self.lab3 = QtWidgets.QLabel('Nsb, Na, Nch, Npt = ', self.main_widget)
	self.lab4 = QtWidgets.QLabel('', self.main_widget)

	self.lab5 = QtWidgets.QLabel('Select Sideband:', self.main_widget)
	self.groupsb = QtWidgets.QButtonGroup(self.main_widget)
	self.radsb = []
	self.radsb.append(QtWidgets.QRadioButton('0, LSB', self.main_widget))
	self.groupsb.addButton(self.radsb[0])
	self.groupsb.setId(self.radsb[0], 0)
	self.radsb.append(QtWidgets.QRadioButton('1, USB', self.main_widget))
	self.groupsb.addButton(self.radsb[1])
	self.groupsb.setId(self.radsb[1], 1)
	self.radsb[0].setChecked(True)

	self.lab6 = QtWidgets.QLabel('Select Antennas:', self.main_widget)
	self.labi = QtWidgets.QLabel('Ant-i', self.main_widget)
	self.groupi = QtWidgets.QButtonGroup(self.main_widget)
	self.radi = []
	for i in range(ma):
	    self.radi.append(QtWidgets.QRadioButton('%d' % i, self.main_widget))
	    self.groupi.addButton(self.radi[i])
	    self.groupi.setId(self.radi[i], i)
	self.radi[0].setChecked(True)

	self.labj = QtWidgets.QLabel('Ant-j', self.main_widget)
	self.groupj = QtWidgets.QButtonGroup(self.main_widget)
	self.radj = []
	for j in range(ma):
	    self.radj.append(QtWidgets.QRadioButton('%d' % j, self.main_widget))
	    self.groupj.addButton(self.radj[j])
	    self.groupj.setId(self.radj[j], j)
	self.radj[0].setChecked(True)

	self.lab7 = QtWidgets.QLabel('Time Range (sec):', self.main_widget)
	self.let0 = QtWidgets.QLineEdit(str(self.tlim[0]), self.main_widget)
	self.let1 = QtWidgets.QLineEdit(str(self.tlim[1]), self.main_widget)
	self.lab8 = QtWidgets.QLabel('Channel Range:', self.main_widget)
	self.lec0 = QtWidgets.QLineEdit(str(self.chlim[0]), self.main_widget)
	self.lec1 = QtWidgets.QLineEdit(str(self.chlim[1]), self.main_widget)
	

	# layouts
	h = QtWidgets.QHBoxLayout(self.main_widget)
	l = QtWidgets.QWidget(self.main_widget)
	r = QtWidgets.QWidget(self.main_widget)
	h.addWidget(l)
	h.addWidget(r)
	v = QtWidgets.QVBoxLayout(r)
	v.addWidget(self.ic)
	g = QtWidgets.QGridLayout(l)
	g.addWidget(btn1, 0, 0)
	g.addWidget(btn2, 0, 1)
	g.addWidget(btn3, 0, 2)
	g.addWidget(self.le, 1, 0, 1, 3)
	g.addWidget(self.lab1, 2, 0)
	g.addWidget(self.lab2, 2, 1, 1, 2)
	g.addWidget(self.lab3, 3, 0)
	g.addWidget(self.lab4, 3, 1)

	sb = QtWidgets.QWidget(self.main_widget)
	g.addWidget(sb, 4, 0, 1, 3)
	hsb = QtWidgets.QHBoxLayout(sb)
	hsb.addWidget(self.lab5)
	hsb.addWidget(self.radsb[0])
	hsb.addWidget(self.radsb[1])

	g.addWidget(self.lab6, 5, 0)
	ai = QtWidgets.QWidget(self.main_widget)
	g.addWidget(ai, 6, 0, 1, 3)
	hai = QtWidgets.QHBoxLayout(ai)
	hai.addWidget(self.labi)
	for i in range(ma):
	    hai.addWidget(self.radi[i])
	aj = QtWidgets.QWidget(self.main_widget)
	g.addWidget(aj, 7, 0, 1, 3)
	haj = QtWidgets.QHBoxLayout(aj)
	haj.addWidget(self.labj)
	for j in range(ma):
	    haj.addWidget(self.radj[j])

	g.addWidget(self.lab7, 8, 0)
	g.addWidget(self.let0, 8, 1)
	g.addWidget(self.let1, 8, 2)
	g.addWidget(self.lab8, 9, 0)
	g.addWidget(self.lec0, 9, 1)
	g.addWidget(self.lec1, 9, 2)


	# central
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        #self.statusBar().showMessage("All hail matplotlib!", 2000)


    def openfile(self):
	fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '.')

	if fname[0]:
	    rpath = os.path.relpath(fname[0])
	    self.le.setText(rpath)
	    self.lab2.setText(rpath)
	    self.fname = rpath


    def loadfile(self):
	fname = self.le.text()
	if (self.fname):
	    pass
	elif (fname != ''):
	    self.fname = fname
	    self.lab2.setText(fname)
	    
	if (self.fname):
	    if (self.fname.find('.oneh5') > -1):
		self.time, self.auto, self.cross = ldoneh5(self.fname)
	    elif (self.fname.find('.timestamp') > -1):
		self.time, self.auto, self.cross = ldcorr(self.fname, self.na)

	    self.nsb, self.na, self.nch, self.npt = self.auto.shape
	    self.lab4.setText(repr(self.auto.shape))
	    self.t2 = self.time - self.time[0]
	    self.tlim = self.t2[0], self.t2[-1]
	    self.let0.setText('%.3f' % self.tlim[0])
	    self.let1.setText('%.3f' % self.tlim[1])
	    self.bl = np.zeros((self.na-1, self.na))	# anti: 0, na-2; antj = 1, na-1
	    b = 0
	    for i in range(self.na-1):
		for j in range(i+1, self.na):
		    b += 1
		    self.bl[i, j] = b

	else:
	    self.statusBar().showMessage("no file selected!", 2000)




    def plotfile(self):
	w = np.logical_and(self.t2 >= self.tlim[0], self.t2 <= self.tlim[1])
	x = self.t2[w]
	anti = self.groupi.checkedId()
	antj = self.groupj.checkedId()
	print anti, antj
	#print 'radio i'
	#for i in range(self.na):
	#    print self.groupi.id(self.radi[i]), self.radi[i].isChecked()
	#print 'radio j'
	#for j in range(self.na):
	#    print self.groupj.id(self.radj[j]), self.radj[j].isChecked()

	if (0<=anti<self.na-1 and 0<=antj<self.na and anti<=antj):
	    if (anti == antj):	# auto
		y = self.auto[0, anti][self.chlim[0]:self.chlim[1], w].mean(axis=0)
	    else:		# cross
		b = self.bl[anti, antj]
		y = np.abs(self.cross[0, b][self.chlim[0]:self.chlim[1], w].mean(axis=0))

	    self.ic.update_figure(x, y)

	else:
	    self.statusBar().showMessage("antenna selection error!", 2000)



    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """embedding_in_qt5.py example
Copyright 2005 Florent Rougon, 2006 Darren Dale, 2015 Jens H Nielsen

This program is a simple example of a Qt5 application embedding matplotlib
canvases.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation.

This is modified from the embedding in qt4 example to show the difference
between qt4 and qt5"""
                                )


qApp = QtWidgets.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()
