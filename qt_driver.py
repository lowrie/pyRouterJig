###########################################################################
#
# Copyright 2015 Robert B. Lowrie (http://github.com/lowrie)
#
# This file is part of pyRouterJig.
#
# pyRouterJig is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pyRouterJig; see the file LICENSE. If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################

'''
Contains the main driver, using pySide or pyQt.
'''
from __future__ import print_function
from builtins import str

import os, sys, traceback, webbrowser

import qt_fig
import router
import spacing
import utils
import doc
from options import OPTIONS

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui

DEBUG = OPTIONS['debug']
WOODS = OPTIONS['woods']

class Driver(QtGui.QMainWindow):
    '''
    Qt driver for pyRouterJig
    '''
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        sys.excepthook = self.exception_hook
        self.except_handled = False

        # Default is English units, 1/32" resolution
        self.units = utils.Units(intervals_per_inch=32)
        self.doc = doc.Doc(self.units)

        # Create an initial joint
        self.bit = router.Router_Bit(self.units, 16, 24)
        self.board = router.Board(self.bit, width=self.units.inches_to_intervals(7.5))
        self.template = router.Incra_Template(self.units, self.board)
        self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board)
        self.equal_spacing.set_cuts()
        self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
        self.var_spacing.set_cuts()
        self.edit_spacing = spacing.Edit_Spaced(self.bit, self.board)
        self.edit_spacing.set_cuts(self.equal_spacing.cuts)
        self.spacing = self.equal_spacing # the default

        # Create the main frame and menus
        self.create_menu()
        self.create_status_bar()
        self.create_widgets()
        self.layout_widgets()

        # Draw the initial figure
        self.draw()

        # Keep track whether the current figure has been saved.  We initialize to true,
        # because we assume that that the user does not want the default joint saved.
        self.file_saved = True

        # The working_dir is where we save screenshots and files.  We start
        # with the user home directory.  Ideally, if using the script to
        # start the program, then we'd use the cwd, but that's complicated.
        self.working_dir = os.path.expanduser('~')

        # We form the screenshot filename from this index
        self.screenshot_index = 0

        self.control_key = False
        self.shift_key = False
        self.alt_key = False

    def exception_hook(self, etype, value, trace):
        '''
        Handler for all exceptions.
        '''
        if self.except_handled:
            return

        self.except_handled = True
        if DEBUG:
            tmp = traceback.format_exception(etype, value, trace)
        else:
            tmp = traceback.format_exception_only(etype, value)
        exception = '\n'.join(tmp)

        QtGui.QMessageBox.warning(self, 'Error', exception)
        self.except_handled = False

    def create_menu(self):
        '''
        Creates the drop-down menus.
        '''
        self.menubar = self.menuBar()

        # always attach the menubar to the application window, even on the Mac
        self.menubar.setNativeMenuBar(False)

        # Add the file menu

        self.file_menu = self.menubar.addMenu('File')

        print_action = QtGui.QAction('&Print', self)
        print_action.setShortcut('Ctrl+P')
        print_action.setStatusTip('Print the figure')
        print_action.triggered.connect(self._on_print)
        self.file_menu.addAction(print_action)

        screenshot_action = QtGui.QAction('&Screenshot', self)
        screenshot_action.setShortcut('Ctrl+S')
        screenshot_action.setStatusTip('Screenshot of window')
        screenshot_action.triggered.connect(self._on_screenshot)
        self.file_menu.addAction(screenshot_action)

        exit_action = QtGui.QAction('&Quit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit pyRouterJig')
        exit_action.triggered.connect(self._on_exit)
        self.file_menu.addAction(exit_action)

        # Add units menu

        self.units_menu = self.menubar.addMenu('Units')
        ag = QtGui.QActionGroup(self, exclusive=True)
        self.english_action = QtGui.QAction('English', self, checkable=True)
        self.units_menu.addAction(ag.addAction(self.english_action))
        self.metric_action = QtGui.QAction('Metric', self, checkable=True)
        self.units_menu.addAction(ag.addAction(self.metric_action))
        self.english_action.setChecked(True)
        self.english_action.triggered.connect(self._on_units)
        self.metric_action.triggered.connect(self._on_units)

        # Add wood menu

        self.wood_menu = self.menubar.addMenu('Wood')
        ag = QtGui.QActionGroup(self, exclusive=True)
        skeys = sorted(WOODS.keys())
        skeys.append('NONE')
        self.wood_actions = {}
        for k in skeys:
            self.wood_actions[k] = QtGui.QAction(k, self, checkable=True)
            self.wood_menu.addAction(ag.addAction(self.wood_actions[k]))
            self.wood_actions[k].triggered.connect(self._on_wood)
        self.wood_actions['Cherry'].setChecked(True)
        self.wood_dir = 'woods/'
        self.board.set_icon(self.wood_dir + WOODS['Cherry'])

        # Add the help menu

        self.help_menu = self.menubar.addMenu('Help')

        about_action = QtGui.QAction('&About', self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip('About this program')
        about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(about_action)

        doclink_action = QtGui.QAction('&Dccumentation', self)
        doclink_action.setStatusTip('Opens documentation page in web browser')
        doclink_action.triggered.connect(self._on_doclink)
        self.help_menu.addAction(doclink_action)

    def create_widgets(self):
        '''
        Creates all of the widgets in the main panel
        '''
        self.main_frame = QtGui.QWidget()

        lineEditWidth = 80

        # Create the figure canvas, using mpl interface
        self.fig = qt_fig.Qt_Fig(self.template, self.board)
        self.fig.canvas.setParent(self.main_frame)
        self.fig.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.fig.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.fig.canvas.setFocus()

        # Board width text box
        self.tb_board_width_label = QtGui.QLabel('Board Width')
        self.tb_board_width = QtGui.QLineEdit(self.main_frame)
        self.tb_board_width.setFixedWidth(lineEditWidth)
        self.tb_board_width.setText(self.units.intervals_to_string(self.board.width))
        self.tb_board_width.editingFinished.connect(self._on_board_width)
        self.tb_board_width.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        # Bit width text box
        self.tb_bit_width_label = QtGui.QLabel('Bit Width')
        self.tb_bit_width = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_width.setFixedWidth(lineEditWidth)
        self.tb_bit_width.setText(self.units.intervals_to_string(self.bit.width))
        self.tb_bit_width.editingFinished.connect(self._on_bit_width)

        # Bit depth text box
        self.tb_bit_depth_label = QtGui.QLabel('Bit Depth')
        self.tb_bit_depth = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_depth.setFixedWidth(lineEditWidth)
        self.tb_bit_depth.setText(self.units.intervals_to_string(self.bit.depth))
        self.tb_bit_depth.editingFinished.connect(self._on_bit_depth)

        # Bit angle text box
        self.tb_bit_angle_label = QtGui.QLabel('Bit Angle')
        self.tb_bit_angle = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_angle.setFixedWidth(lineEditWidth)
        self.tb_bit_angle.setText('%g' % self.bit.angle)
        self.tb_bit_angle.editingFinished.connect(self._on_bit_angle)

        # Save button
        #self.btn_print = QtGui.QPushButton('Print', self.main_frame)
        #self.btn_print.clicked.connect(self._on_print)

        # Equal spacing widgets

        params = self.equal_spacing.get_params()
        labels = self.equal_spacing.full_labels
        self.es_cut_values = [0] * 3

        # ...first slider
        p = params[0]
        self.es_cut_values[0] = p.vInit
        self.es_slider0_label = QtGui.QLabel(labels[0])
        self.es_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider0.setMinimum(p.vMin)
        self.es_slider0.setMaximum(p.vMax)
        self.es_slider0.setValue(p.vInit)
        self.es_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.es_slider0.setTickInterval(1)
        self.es_slider0.valueChanged.connect(self._on_es_slider0)
        self.es_slider0.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # ...second slider
        p = params[1]
        self.es_cut_values[1] = p.vInit
        self.es_slider1_label = QtGui.QLabel(labels[1])
        self.es_slider1 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider1.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider1.setMinimum(p.vMin)
        self.es_slider1.setMaximum(p.vMax)
        self.es_slider1.setValue(p.vInit)
        self.es_slider1.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.es_slider1.setTickInterval(1)
        self.es_slider1.valueChanged.connect(self._on_es_slider1)
        self.es_slider1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # ...check box for centering
        p = params[2]
        self.es_cut_values[2] = p.vInit
        self.cb_es_centered = QtGui.QCheckBox(labels[2], self.main_frame)
        self.cb_es_centered.setChecked(True)
        self.cb_es_centered.stateChanged.connect(self._on_cb_es_centered)

        # Variable spacing widgets

        params = self.var_spacing.get_params()
        labels = self.var_spacing.full_labels
        self.vs_cut_values = [0] * 2

        # ...slider
        p = params[0]
        self.vs_cut_values[0] = p.vInit
        self.vs_slider0_label = QtGui.QLabel(labels[0])
        self.vs_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.vs_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.vInit)
        self.vs_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.vs_slider0.setTickInterval(1)
        self.vs_slider0.valueChanged.connect(self._on_vs_slider0)
        self.vs_slider0.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # Edit spacing widgets (nothing yet)

        params = self.edit_spacing.get_params()
        labels = self.edit_spacing.full_labels
        self.cs_cut_values = []

        self.set_tooltips()

    def set_tooltips(self):
        '''
        [Re]sets the tool tips for the widgets
        '''
        self.tb_board_width.setToolTip(self.doc.board_width())
        self.tb_bit_width.setToolTip(self.doc.bit_width())
        self.tb_bit_depth.setToolTip(self.doc.bit_depth())
        self.tb_bit_angle.setToolTip(self.doc.bit_angle())
        self.es_slider0.setToolTip(self.doc.es_slider0())
        self.es_slider1.setToolTip(self.doc.es_slider1())
        self.cb_es_centered.setToolTip(self.doc.es_centered())
        self.vs_slider0.setToolTip(self.doc.vs_slider0())
        #self.btn_print.setToolTip('Print the figure')

    def layout_widgets(self):
        '''
        Does the layout of the widgets in the main frame
        '''

        # vbox contains all of the widgets in the main frame, positioned
        # vertically
        self.vbox = QtGui.QVBoxLayout()

        # Add the figure canvas to the top
        self.vbox.addWidget(self.fig.canvas)

        # hbox contains all of the control widgets
        # (everything but the canvas)
        self.hbox = QtGui.QHBoxLayout()

        # Add the board width label, board width input text box,
        # all stacked vertically on the left side.
        self.vbox_board_width = QtGui.QVBoxLayout()
        self.vbox_board_width.addWidget(self.tb_board_width_label)
        self.vbox_board_width.addWidget(self.tb_board_width)
        self.vbox_board_width.addStretch(1)
#        self.vbox_board_width.addWidget(self.btn_print)
        self.hbox.addLayout(self.vbox_board_width)

        # Add the bit width label and its text box
        self.vbox_bit_width = QtGui.QVBoxLayout()
        self.vbox_bit_width.addWidget(self.tb_bit_width_label)
        self.vbox_bit_width.addWidget(self.tb_bit_width)
        self.vbox_bit_width.addStretch(1)
        self.hbox.addLayout(self.vbox_bit_width)

        # Add the bit depth label and its text box
        self.vbox_bit_depth = QtGui.QVBoxLayout()
        self.vbox_bit_depth.addWidget(self.tb_bit_depth_label)
        self.vbox_bit_depth.addWidget(self.tb_bit_depth)
        self.vbox_bit_depth.addStretch(1)
        self.hbox.addLayout(self.vbox_bit_depth)

        # Add the bit angle label and its text box
        self.vbox_bit_angle = QtGui.QVBoxLayout()
        self.vbox_bit_angle.addWidget(self.tb_bit_angle_label)
        self.vbox_bit_angle.addWidget(self.tb_bit_angle)
        self.vbox_bit_angle.addStretch(1)
        self.hbox.addLayout(self.vbox_bit_angle)

        # Create the layout of the Equal spacing controls
        self.hbox_es = QtGui.QHBoxLayout()

        self.vbox_es_slider0 = QtGui.QVBoxLayout()
        self.vbox_es_slider0.addWidget(self.es_slider0_label)
        self.vbox_es_slider0.addWidget(self.es_slider0)
        self.hbox_es.addLayout(self.vbox_es_slider0)

        self.vbox_es_slider1 = QtGui.QVBoxLayout()
        self.vbox_es_slider1.addWidget(self.es_slider1_label)
        self.vbox_es_slider1.addWidget(self.es_slider1)
        self.hbox_es.addLayout(self.vbox_es_slider1)

        self.hbox_es.addWidget(self.cb_es_centered)

        # Create the layout of the Variable spacing controls.  Given only one
        # item, this is overkill, but the coding allows us to add additional
        # controls later.
        self.hbox_vs = QtGui.QHBoxLayout()

        self.vbox_vs_slider0 = QtGui.QVBoxLayout()
        self.vbox_vs_slider0.addWidget(self.vs_slider0_label)
        self.vbox_vs_slider0.addWidget(self.vs_slider0)
        self.hbox_vs.addLayout(self.vbox_vs_slider0)

        # Create the layout of the edit spacing controls
        self.hbox_cs = QtGui.QHBoxLayout()

        # Add the spacing layouts as Tabs
        self.tabs_spacing = QtGui.QTabWidget()
        self.tab_es = QtGui.QWidget()
        self.tab_es.setLayout(self.hbox_es)
        self.tabs_spacing.addTab(self.tab_es, 'Equal')
        self.tab_vs = QtGui.QWidget()
        self.tab_vs.setLayout(self.hbox_vs)
        self.tabs_spacing.addTab(self.tab_vs, 'Variable')
        self.tab_cs = QtGui.QWidget()
        self.tab_cs.setLayout(self.hbox_cs)
        self.tabs_spacing.addTab(self.tab_cs, 'Editor')
        self.tabs_spacing.currentChanged.connect(self._on_tabs_spacing)
        tip = 'These tabs specify the layout algorithm for the fingers.'
        self.tabs_spacing.setToolTip(tip)

        # either add the spacing Tabs to the bottom
        #self.vbox.addLayout(self.hbox)
        #self.vbox.addWidget(self.tabs_spacing)
        # ... or to the right of the text boxes
        self.hbox.addWidget(self.tabs_spacing)
        self.vbox.addStretch(1)
        self.vbox.addLayout(self.hbox)
#        self.vbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        # Lay it all out
        self.main_frame.setLayout(self.vbox)
        self.setCentralWidget(self.main_frame)

    def create_status_bar(self):
        '''
        Creates a status message bar that is placed at the bottom of the
        main frame.
        '''
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Ready')

    def draw(self):
        '''(Re)draws the template and boards'''
        if DEBUG:
            print('draw')
        self.template = router.Incra_Template(self.units, self.board)
        self.fig.draw(self.template, self.board, self.bit, self.spacing)

    def reinit_spacing(self):
        '''
        Re-initializes the joint spacing objects.  This must be called
        when the router bit or board change dimensions.
        '''

        # The ordering of the index is the same order that the tabs
        # were created in create main frame
        spacing_index = self.tabs_spacing.currentIndex()

        # enable/disable editing of line edit boxes, depending upon spacing
        # algorithm
        tbs = [self.tb_board_width, self.tb_bit_width, self.tb_bit_depth,\
               self.tb_bit_angle]
        if spacing_index == 2:
            print('setting read only')
            for tb in tbs:
                tb.setEnabled(False)
                tb.setStyleSheet("color: rgb(200, 200, 200);")
        else:
            print('unsetting read only')
            for tb in tbs:
                tb.setEnabled(True)
                tb.setStyleSheet("color: rgb(0, 0, 0);")

        # Set up the widgets for each spacing algorithm
        if spacing_index == 0:
            # do the equal spacing parameters.  Preserve the centered option.
            self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board)
            params = self.equal_spacing.get_params()
            p = params[0]
            self.es_slider0.blockSignals(True)
            self.es_slider0.setMinimum(p.vMin)
            self.es_slider0.setMaximum(p.vMax)
            self.es_slider0.setValue(p.vInit)
            self.es_slider0.blockSignals(False)
            self.es_cut_values[0] = p.vInit
            p = params[1]
            self.es_slider1.blockSignals(True)
            self.es_slider1.setMinimum(p.vMin)
            self.es_slider1.setMaximum(p.vMax)
            self.es_slider1.setValue(p.vInit)
            self.es_slider1.blockSignals(False)
            self.es_cut_values[1] = p.vInit
            p = params[2]
            centered = self.es_cut_values[2]
            self.cb_es_centered.blockSignals(True)
            self.cb_es_centered.setChecked(centered)
            self.cb_es_centered.blockSignals(False)
            self.equal_spacing.set_cuts(self.es_cut_values)
            self.es_slider0_label.setText(self.equal_spacing.full_labels[0])
            self.es_slider1_label.setText(self.equal_spacing.full_labels[1])
            self.spacing = self.equal_spacing
        elif spacing_index == 1:
            # do the variable spacing parameters
            self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
            params = self.var_spacing.get_params()
            p = params[0]
            self.vs_slider0.blockSignals(True)
            self.vs_slider0.setMinimum(p.vMin)
            self.vs_slider0.setMaximum(p.vMax)
            self.vs_slider0.setValue(p.vInit)
            self.vs_slider0.blockSignals(False)
            self.vs_cut_values[0] = p.vInit
            self.var_spacing.set_cuts(self.vs_cut_values)
            self.vs_slider0_label.setText(self.var_spacing.full_labels[0])
            self.spacing = self.var_spacing
        elif spacing_index == 2:
            # Do the edit spacing parameters.  Currently, this has no
            # parameters, and uses as a starting spacing whatever the previous
            # spacing set.
            self.edit_spacing = spacing.Edit_Spaced(self.bit, self.board)
            self.edit_spacing.set_cuts(self.spacing.cuts)
            params = self.edit_spacing.get_params()
            self.spacing = self.edit_spacing
        else:
            raise ValueError('Bad value for spacing_index %d' % spacing_index)

    @QtCore.pyqtSlot(int)
    def _on_tabs_spacing(self, index):
        '''Handles changes to spacing algorithm'''
        if DEBUG:
            print('_on_tabs_spacing')
        self.reinit_spacing()
        self.draw()
        self.status_message('Changed to spacing algorithm %s'\
                            % str(self.tabs_spacing.tabText(index)))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_width(self):
        '''Handles changes to bit width'''
        if DEBUG:
            print('_on_bit_width')
        # With editingFinished, we also need to check whether the
        # value actually changed. This is because editingFinished gets
        # triggered every time focus changes, which can occur many
        # times when an exception is thrown, or user tries to quit
        # in the middle of an exception, etc.  This logic also avoids
        # unnecessary redraws.
        if self.tb_bit_width.isModified():
            if DEBUG:
                print(' bit_width modified')
            self.tb_bit_width.setModified(False)
            text = str(self.tb_bit_width.text())
            self.bit.set_width_from_string(text)
            self.reinit_spacing()
            self.draw()
            self.status_message('Changed bit width to ' + text)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_depth(self):
        '''Handles changes to bit depth'''
        if DEBUG:
            print('_on_bit_depth')
        if self.tb_bit_depth.isModified():
            self.tb_bit_depth.setModified(False)
            text = str(self.tb_bit_depth.text())
            self.bit.set_depth_from_string(text)
            self.board.set_height(self.bit)
            self.draw()
            self.status_message('Changed bit depth to ' + text)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_angle(self):
        '''Handles changes to bit angle'''
        if DEBUG:
            print('_on_bit_angle')
        if self.tb_bit_angle.isModified():
            self.tb_bit_angle.setModified(False)
            text = str(self.tb_bit_angle.text())
            self.bit.set_angle_from_string(text)
            self.reinit_spacing()
            self.draw()
            self.status_message('Changed bit angle to ' + text)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_board_width(self):
        '''Handles changes to board width'''
        if DEBUG:
            print('_on_board_width')
        if self.tb_board_width.isModified():
            self.tb_board_width.setModified(False)
            text = str(self.tb_board_width.text())
            self.board.set_width_from_string(text)
            self.reinit_spacing()
            self.draw()
            self.status_message('Changed board width to ' + text)
            self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_es_slider0(self, value):
        '''Handles changes to the equally-spaced slider B-spacing'''
        if DEBUG:
            print('_on_es_slider0', value)
        self.es_cut_values[0] = value
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.es_slider0_label.setText(self.equal_spacing.full_labels[0])
        self.draw()
        self.status_message('Changed slider %s' % str(self.es_slider0_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_es_slider1(self, value):
        '''Handles changes to the equally-spaced slider Width'''
        if DEBUG:
            print('_on_es_slider1', value)
        self.es_cut_values[1] = value
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.es_slider1_label.setText(self.equal_spacing.full_labels[1])
        self.draw()
        self.status_message('Changed slider %s' % str(self.es_slider1_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_cb_es_centered(self):
        '''Handles changes to centered checkbox'''
        if DEBUG:
            print('_on_cb_es_centered')
        self.es_cut_values[2] = self.cb_es_centered.isChecked()
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.draw()
        if self.es_cut_values[2]:
            self.status_message('Checked Centered.')
        else:
            self.status_message('Unchecked Centered.')
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_vs_slider0(self, value):
        '''Handles changes to the variable-spaced slider Fingers'''
        if DEBUG:
            print('_on_vs_slider0', value)
        self.vs_cut_values[0] = value
        self.var_spacing.set_cuts(self.vs_cut_values)
        self.vs_slider0_label.setText(self.var_spacing.full_labels[0])
        self.draw()
        self.status_message('Changed slider %s' % str(self.vs_slider0_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_print(self):
        '''Handles print events'''
        if DEBUG:
            print('_on_print')

        r = self.fig.print(self.template, self.board, self.bit, self.spacing)
        if r:
            self.status_message("Figure printed")
        else:
            self.status_message("Figure not printed")

    @QtCore.pyqtSlot()
    def _on_screenshot(self):
        '''Handles screenshot events'''
        if DEBUG:
            print('_on_screenshot')
        filetype = 'png'
        filename = os.path.join(self.working_dir,
                                'screenshot_%d.%s' % (self.screenshot_index, filetype))
        QtGui.QPixmap.grabWindow(self.winId()).save(filename, filetype)
        self.status_message("Saved screenshot to %s" % filename)
        self.screenshot_index += 1

    @QtCore.pyqtSlot()
    def _on_exit(self):
        '''Handles code exit events'''
        if DEBUG:
            print('_on_exit')
        if self.file_saved:
            QtGui.qApp.quit()
        else:
            msg = 'Figure was changed but not saved.  Are you sure you want to quit?'
            reply = QtGui.QMessageBox.question(self, 'Message', msg,
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                QtGui.qApp.quit()

    @QtCore.pyqtSlot()
    def _on_about(self):
        '''Handles about dialog event'''
        if DEBUG:
            print('_on_about')

        box = QtGui.QMessageBox(self)
        s = '<h2>Welcome to pyRouterJig!</h2>'
        s += '<h3>Version: %s</h3>' % utils.VERSION
        box.setText(s + self.doc.short_desc() + self.doc.license())
        box.setTextFormat(QtCore.Qt.RichText)
        box.show()

    @QtCore.pyqtSlot()
    def _on_doclink(self):
        '''Handles doclink event'''
        if DEBUG:
            print('_on_doclink')

        webbrowser.open('http://lowrie.github.io/pyRouterJig/documentation.html')

    @QtCore.pyqtSlot()
    def _on_units(self):
        '''Handles changes in units'''
        if DEBUG:
            print('_on_units')
        do_metric = self.metric_action.isChecked()
        if self.metric == do_metric:
            return # no change in units
        if do_metric:
            self.units = utils.Units(metric=True)
        else:
            self.units = utils.Units(32)
        self.board.change_units(self.units)
        self.bit.change_units(self.units)
        self.doc.change_units(self.units)
        self.tb_board_width.setText(self.units.intervals_to_string(self.board.width))
        self.tb_bit_width.setText(self.units.intervals_to_string(self.bit.width))
        self.tb_bit_depth.setText(self.units.intervals_to_string(self.bit.depth))
        self.reinit_spacing()
        self.set_tooltips()
        self.draw()

    @QtCore.pyqtSlot()
    def _on_wood(self):
        '''Handles changes in wood'''
        if DEBUG:
            print('_on_wood')
        for k, v in self.wood_actions.items():
            if v.isChecked():
                wood = k
                break
        if wood == 'NONE':
            self.board.set_icon(None)
        else:
            self.board.set_icon(self.wood_dir + WOODS[wood])
        self.draw()

    def status_message(self, msg, flash_len_ms=None):
        '''Flashes a status message to the status bar'''
        self.statusbar.showMessage(msg)
        if flash_len_ms is not None:
            QtCore.QTimer.singleShot(flash_len_ms, self._on_flash_status_off)

    @QtCore.pyqtSlot()
    def _on_flash_status_off(self):
        '''Handles event to turn off statusbar message'''
        if DEBUG:
            print('_on_flash_status_off')
        self.statusbar.showMessage('')

    def closeEvent(self, event):
        '''
        For closeEvents (user closes window or presses Ctrl-Q), ignore and call
        _on_exit()
        '''
        if DEBUG:
            print('closeEvent')
        self._on_exit()
        event.ignore()

    def keyPressEvent(self, event):
        '''
        Handles key press events
        '''
        # return if not edit spacing
        if self.tabs_spacing.currentIndex() != 2:
            event.ignore()
            return
        
        msg = None
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = True
        elif event.key() == QtCore.Qt.Key_Control:
            self.control_key = True
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = True
        elif event.key() == QtCore.Qt.Key_Left:
            if self.shift_key:
                msg = self.spacing.finger_widen_left()
            elif self.control_key:
                msg = self.spacing.finger_trim_left()
            elif self.alt_key:
                msg = self.spacing.finger_increment_active(-1)
            else:
                msg = self.spacing.finger_shift_left()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.shift_key:
                msg = self.spacing.finger_widen_right()
            elif self.control_key:
                msg = self.spacing.finger_trim_right()
            elif self.alt_key:
                msg = self.spacing.finger_increment_active(1)
            else:
                msg = self.spacing.finger_shift_right()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Minus:
            msg = self.spacing.finger_delete_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Plus:
            msg = self.spacing.finger_add()
            self.draw()
        else:
            msg = 'You pressed an unrecognized key: '
            s = event.text()
            if len(s) > 0:
                msg += s
            else:
                msg += '%x' % event.key()
        if msg is not None:
            self.status_message(msg)

    def keyReleaseEvent(self, event):
        '''
        Handles key release events
        '''
        # return if not edit spacing
        if self.tabs_spacing.currentIndex() != 2:
            event.ignore()
            return
            
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = False
        elif event.key() == QtCore.Qt.Key_Control:
            self.control_key = False
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = False
        else:
            if DEBUG:
                print('you released %x' % event.key())

def run():
    '''
    Sets up and runs the application
    '''
    app = QtGui.QApplication(sys.argv)
#    app.setStyle('plastique')
#    app.setStyle('windows')
    driver = Driver()
    driver.show()
    driver.raise_()
    app.exec_()

if __name__ == '__main__':
    run()
