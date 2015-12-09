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
import config_file
import router
import spacing
import utils
import doc
import serialize

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui

def create_vline():
    '''Creates a vertical line'''
    vline = QtGui.QFrame()
    vline.setFrameStyle(QtGui.QFrame.VLine)
    vline.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    return vline

def create_hline():
    '''Creates a horizontal line'''
    hline = QtGui.QFrame()
    hline.setFrameStyle(QtGui.QFrame.HLine)
    hline.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    return hline

class Driver(QtGui.QMainWindow):
    '''
    Qt driver for pyRouterJig
    '''
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        sys.excepthook = self.exception_hook
        self.except_handled = False

        # Read the config file.  We wait until the end of this init to print
        # the status message, because we need it to be created first.
        (self.config, msg) = config_file.read_config()

        # Default is English units, 1/32" resolution
        self.units = utils.Units(self.config.increments_per_inch, self.config.metric)
        self.doc = doc.Doc(self.units)

        # Create an initial joint.  Even though another joint may be opened
        # later, we do this now so that the initial widget layout may be
        # created.
        self.bit = router.Router_Bit(self.units, self.config.bit_width,\
                                     self.config.bit_depth, self.config.bit_angle)
        self.board = router.Board(self.bit, width=self.config.board_width)
        self.template = router.Incra_Template(self.units, self.board)
        self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board, self.config)
        self.equal_spacing.set_cuts()
        self.var_spacing = spacing.Variable_Spaced(self.bit, self.board, self.config)
        self.var_spacing.set_cuts()
        self.edit_spacing = spacing.Edit_Spaced(self.bit, self.board, self.config)
        self.edit_spacing.set_cuts(self.equal_spacing.cuts)
        self.spacing = self.equal_spacing # the default
        self.spacing_index = None # to be set in layout_widgets()

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

        # The working_dir is where we save files.  We start with the user home
        # directory.  Ideally, if using the script to start the program, then
        # we'd use the cwd, but that's complicated.
        self.working_dir = os.path.expanduser('~')

        # We form the screenshot and save filename from this index
        self.screenshot_index = 0

        # Initialize keyboard modifiers
        self.control_key = False
        self.shift_key = False
        self.alt_key = False

        # ... show the status message from reading the configuration file
        self.statusbar.showMessage(msg)

    def exception_hook(self, etype, value, trace):
        '''
        Handler for all exceptions.
        '''
        if self.except_handled:
            return

        self.except_handled = True
        if self.config.debug:
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

        file_menu = self.menubar.addMenu('File')

        open_action = QtGui.QAction('&Open File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Opens a previously saved image of joint')
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QtGui.QAction('&Save File...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Saves an image of the joint to a file')
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        screenshot_action = QtGui.QAction('Screenshot...', self)
        screenshot_action.setShortcut('Ctrl+W')
        screenshot_action.setStatusTip('Saves an image of the pyRouterJig window to a file')
        screenshot_action.triggered.connect(self._on_screenshot)
        file_menu.addAction(screenshot_action)

        print_action = QtGui.QAction('&Print', self)
        print_action.setShortcut('Ctrl+P')
        print_action.setStatusTip('Print the figure')
        print_action.triggered.connect(self._on_print)
        file_menu.addAction(print_action)

        exit_action = QtGui.QAction('&Quit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit pyRouterJig')
        exit_action.triggered.connect(self._on_exit)
        file_menu.addAction(exit_action)

        # Add units menu

        units_menu = self.menubar.addMenu('Units')
        ag = QtGui.QActionGroup(self, exclusive=True)
        english_action = QtGui.QAction('English', self, checkable=True)
        units_menu.addAction(ag.addAction(english_action))
        self.metric_action = QtGui.QAction('Metric', self, checkable=True)
        units_menu.addAction(ag.addAction(self.metric_action))
        english_action.setChecked(True)
        english_action.triggered.connect(self._on_units)
        self.metric_action.triggered.connect(self._on_units)

        # Add wood menu

        wood_menu = self.menubar.addMenu('Wood')
        ag = QtGui.QActionGroup(self, exclusive=True)
        self.wood_actions = {}
        # Add woods from config file, which are image files
        self.woods = utils.create_wood_dict(self.config.wood_images)
        skeys = sorted(self.woods.keys())
        for k in skeys:
            self.wood_actions[k] = QtGui.QAction(k, self, checkable=True)
            wood_menu.addAction(ag.addAction(self.wood_actions[k]))
            self.wood_actions[k].triggered.connect(self._on_wood)
        if len(skeys) > 0:
            wood_menu.addSeparator()
        # Next add patterns
        patterns = {'DiagCrossPattern':QtCore.Qt.DiagCrossPattern,\
                    'BDiagPattern':QtCore.Qt.BDiagPattern,\
                    'FDiagPattern':QtCore.Qt.FDiagPattern,\
                    'Dense1Pattern':QtCore.Qt.Dense1Pattern,\
                    'Dense5Pattern':QtCore.Qt.Dense5Pattern}
        skeys = sorted(patterns.keys())
        for k in skeys:
            self.woods[k] = patterns[k]
            self.wood_actions[k] = QtGui.QAction(k, self, checkable=True)
            wood_menu.addAction(ag.addAction(self.wood_actions[k]))
            self.wood_actions[k].triggered.connect(self._on_wood)
        defwood = 'DiagCrossPattern'
        if self.config.default_wood in self.woods.keys():
            defwood = self.config.default_wood
        self.wood_actions[defwood].setChecked(True)
        self.board.set_icon(self.woods[defwood])

        # Add the help menu

        help_menu = self.menubar.addMenu('Help')

        about_action = QtGui.QAction('&About', self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip('About this program')
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

        doclink_action = QtGui.QAction('&Documentation', self)
        doclink_action.setStatusTip('Opens documentation page in web browser')
        doclink_action.triggered.connect(self._on_doclink)
        help_menu.addAction(doclink_action)

    def create_widgets(self):
        '''
        Creates all of the widgets in the main panel
        '''
        self.main_frame = QtGui.QWidget()

        lineEditWidth = 80

        # Create the figure canvas, using mpl interface
        self.fig = qt_fig.Qt_Fig(self.template, self.board, self.config)
        self.fig.canvas.setParent(self.main_frame)
        self.fig.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.fig.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.fig.canvas.setFocus()

        # Board width text box
        self.tb_board_width_label = QtGui.QLabel('Board Width')
        self.tb_board_width = QtGui.QLineEdit(self.main_frame)
        self.tb_board_width.setFixedWidth(lineEditWidth)
        self.tb_board_width.setText(self.units.increments_to_string(self.board.width))
        self.tb_board_width.editingFinished.connect(self._on_board_width)
        self.tb_board_width.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        # Bit width text box
        self.tb_bit_width_label = QtGui.QLabel('Bit Width')
        self.tb_bit_width = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_width.setFixedWidth(lineEditWidth)
        self.tb_bit_width.setText(self.units.increments_to_string(self.bit.width))
        self.tb_bit_width.editingFinished.connect(self._on_bit_width)

        # Bit depth text box
        self.tb_bit_depth_label = QtGui.QLabel('Bit Depth')
        self.tb_bit_depth = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_depth.setFixedWidth(lineEditWidth)
        self.tb_bit_depth.setText(self.units.increments_to_string(self.bit.depth))
        self.tb_bit_depth.editingFinished.connect(self._on_bit_depth)

        # Bit angle text box
        self.tb_bit_angle_label = QtGui.QLabel('Bit Angle')
        self.tb_bit_angle = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_angle.setFixedWidth(lineEditWidth)
        self.tb_bit_angle.setText('%g' % self.bit.angle)
        self.tb_bit_angle.editingFinished.connect(self._on_bit_angle)

        # Equal spacing widgets

        params = self.equal_spacing.params
        labels = self.equal_spacing.labels

        # ...first slider
        p = params['B-spacing']
        self.es_slider0_label = QtGui.QLabel(labels[0])
        self.es_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider0.setMinimum(p.vMin)
        self.es_slider0.setMaximum(p.vMax)
        self.es_slider0.setValue(p.v)
        self.es_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.es_slider0.setTickInterval(1)
        self.es_slider0.valueChanged.connect(self._on_es_slider0)
        self.es_slider0.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # ...second slider
        p = params['Width']
        self.es_slider1_label = QtGui.QLabel(labels[1])
        self.es_slider1 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider1.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider1.setMinimum(p.vMin)
        self.es_slider1.setMaximum(p.vMax)
        self.es_slider1.setValue(p.v)
        self.es_slider1.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.es_slider1.setTickInterval(1)
        self.es_slider1.valueChanged.connect(self._on_es_slider1)
        self.es_slider1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # ...check box for centering
        p = params['Centered']
        self.cb_es_centered = QtGui.QCheckBox(labels[2], self.main_frame)
        self.cb_es_centered.setChecked(True)
        self.cb_es_centered.stateChanged.connect(self._on_cb_es_centered)

        # Variable spacing widgets

        params = self.var_spacing.params
        labels = self.var_spacing.labels

        # ...slider
        p = params['Fingers']
        self.vs_slider0_label = QtGui.QLabel(labels[0])
        self.vs_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.vs_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.v)
        self.vs_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        if p.vMax - p.vMin < 10:
            self.vs_slider0.setTickInterval(1)
        self.vs_slider0.valueChanged.connect(self._on_vs_slider0)
        self.vs_slider0.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # Edit spacing widgets

        self.edit_btn_undo = QtGui.QPushButton('Undo', self.main_frame)
        self.edit_btn_undo.clicked.connect(self._on_edit_undo)
        self.edit_btn_undo.setToolTip('Undo the last change')
        self.edit_btn_add = QtGui.QPushButton('Add', self.main_frame)
        self.edit_btn_add.clicked.connect(self._on_edit_add)
        self.edit_btn_add.setToolTip('Add a finger (if there is space to add fingers)')
        self.edit_btn_del = QtGui.QPushButton('Delete', self.main_frame)
        self.edit_btn_del.clicked.connect(self._on_edit_del)
        self.edit_btn_del.setToolTip('Delete the active fingers')

        self.edit_move_label = QtGui.QLabel('Move')
        self.edit_move_label.setToolTip('Moves the active fingers')
        self.edit_btn_moveL = QtGui.QToolButton(self.main_frame)
        self.edit_btn_moveL.setArrowType(QtCore.Qt.LeftArrow)
        self.edit_btn_moveL.clicked.connect(self._on_edit_moveL)
        self.edit_btn_moveL.setToolTip('Move active fingers to left 1 increment')
        self.edit_btn_moveR = QtGui.QToolButton(self.main_frame)
        self.edit_btn_moveR.setArrowType(QtCore.Qt.RightArrow)
        self.edit_btn_moveR.clicked.connect(self._on_edit_moveR)
        self.edit_btn_moveR.setToolTip('Move active fingers to right 1 increment')

        self.edit_widen_label = QtGui.QLabel('Widen')
        self.edit_widen_label.setToolTip('Widens the active fingers')
        self.edit_btn_widenL = QtGui.QToolButton(self.main_frame)
        self.edit_btn_widenL.setArrowType(QtCore.Qt.LeftArrow)
        self.edit_btn_widenL.clicked.connect(self._on_edit_widenL)
        self.edit_btn_widenL.setToolTip('Widen active fingers 1 increment on left side')
        self.edit_btn_widenR = QtGui.QToolButton(self.main_frame)
        self.edit_btn_widenR.setArrowType(QtCore.Qt.RightArrow)
        self.edit_btn_widenR.clicked.connect(self._on_edit_widenR)
        self.edit_btn_widenR.setToolTip('Widen active fingers 1 increment on right side')

        self.edit_trim_label = QtGui.QLabel('Trim')
        self.edit_trim_label.setToolTip('Trims the active fingers')
        self.edit_btn_trimL = QtGui.QToolButton(self.main_frame)
        self.edit_btn_trimL.setArrowType(QtCore.Qt.LeftArrow)
        self.edit_btn_trimL.clicked.connect(self._on_edit_trimL)
        self.edit_btn_trimL.setToolTip('Trim active fingers 1 increment on left side')
        self.edit_btn_trimR = QtGui.QToolButton(self.main_frame)
        self.edit_btn_trimR.setArrowType(QtCore.Qt.RightArrow)
        self.edit_btn_trimR.clicked.connect(self._on_edit_trimR)
        self.edit_btn_trimR.setToolTip('Trim active fingers 1 increment on right side')

        self.edit_btn_toggle = QtGui.QPushButton('Toggle', self.main_frame)
        self.edit_btn_toggle.clicked.connect(self._on_edit_toggle)
        self.edit_btn_toggle.setToolTip('Toggles the finger at cursor between active and deactive')
        self.edit_btn_cursorL = QtGui.QToolButton(self.main_frame)
        self.edit_btn_cursorL.setArrowType(QtCore.Qt.LeftArrow)
        self.edit_btn_cursorL.clicked.connect(self._on_edit_cursorL)
        self.edit_btn_cursorL.setToolTip('Move finger cursor to left')
        self.edit_btn_cursorR = QtGui.QToolButton(self.main_frame)
        self.edit_btn_cursorR.setArrowType(QtCore.Qt.RightArrow)
        self.edit_btn_cursorR.clicked.connect(self._on_edit_cursorR)
        self.edit_btn_cursorR.setToolTip('Move finger cursor to right')
        self.edit_btn_activate_all = QtGui.QPushButton('All', self.main_frame)
        self.edit_btn_activate_all.clicked.connect(self._on_edit_activate_all)
        self.edit_btn_activate_all.setToolTip('Set all fingers to be active')
        self.edit_btn_deactivate_all = QtGui.QPushButton('None', self.main_frame)
        self.edit_btn_deactivate_all.clicked.connect(self._on_edit_deactivate_all)
        self.edit_btn_deactivate_all.setToolTip('Set no fingers to be active')

        self.update_tooltips()

    def update_tooltips(self):
        '''
        [Re]sets the tool tips for the widgets
        '''
        self.tb_board_width.setToolTip(self.doc.board_width())
        self.tb_bit_width.setToolTip(self.doc.bit_width())
        self.tb_bit_depth.setToolTip(self.doc.bit_depth())
        self.tb_bit_angle.setToolTip(self.doc.bit_angle())
        self.es_slider0_label.setToolTip(self.doc.es_slider0())
        self.es_slider0.setToolTip(self.doc.es_slider0())
        self.es_slider1_label.setToolTip(self.doc.es_slider1())
        self.es_slider1.setToolTip(self.doc.es_slider1())
        self.cb_es_centered.setToolTip(self.doc.es_centered())
        self.vs_slider0_label.setToolTip(self.doc.vs_slider0())
        self.vs_slider0.setToolTip(self.doc.vs_slider0())

    def layout_widgets(self):
        '''
        Does the layout of the widgets in the main frame
        '''

        # vbox contains all of the widgets in the main frame, positioned
        # vertically
        vbox = QtGui.QVBoxLayout()

        # Add the figure canvas to the top
        vbox.addWidget(self.fig.canvas)

        # hbox contains all of the control widgets
        # (everything but the canvas)
        hbox = QtGui.QHBoxLayout()

        # Add the board width label, board width input text box,
        # all stacked vertically on the left side.
        vbox_board_width = QtGui.QVBoxLayout()
        vbox_board_width.addWidget(self.tb_board_width_label)
        vbox_board_width.addWidget(self.tb_board_width)
        vbox_board_width.addStretch(1)
        hbox.addLayout(vbox_board_width)

        # Add the bit width label and its text box
        vbox_bit_width = QtGui.QVBoxLayout()
        vbox_bit_width.addWidget(self.tb_bit_width_label)
        vbox_bit_width.addWidget(self.tb_bit_width)
        vbox_bit_width.addStretch(1)
        hbox.addLayout(vbox_bit_width)

        # Add the bit depth label and its text box
        vbox_bit_depth = QtGui.QVBoxLayout()
        vbox_bit_depth.addWidget(self.tb_bit_depth_label)
        vbox_bit_depth.addWidget(self.tb_bit_depth)
        vbox_bit_depth.addStretch(1)
        hbox.addLayout(vbox_bit_depth)

        # Add the bit angle label and its text box
        vbox_bit_angle = QtGui.QVBoxLayout()
        vbox_bit_angle.addWidget(self.tb_bit_angle_label)
        vbox_bit_angle.addWidget(self.tb_bit_angle)
        vbox_bit_angle.addStretch(1)
        hbox.addLayout(vbox_bit_angle)

        # Create the layout of the Equal spacing controls
        hbox_es = QtGui.QHBoxLayout()

        vbox_es_slider0 = QtGui.QVBoxLayout()
        vbox_es_slider0.addWidget(self.es_slider0_label)
        vbox_es_slider0.addWidget(self.es_slider0)
        hbox_es.addLayout(vbox_es_slider0)

        vbox_es_slider1 = QtGui.QVBoxLayout()
        vbox_es_slider1.addWidget(self.es_slider1_label)
        vbox_es_slider1.addWidget(self.es_slider1)
        hbox_es.addLayout(vbox_es_slider1)

        hbox_es.addWidget(self.cb_es_centered)

        # Create the layout of the Variable spacing controls.  Given only one
        # item, this is overkill, but the coding allows us to add additional
        # controls later.
        hbox_vs = QtGui.QHBoxLayout()

        vbox_vs_slider0 = QtGui.QVBoxLayout()
        vbox_vs_slider0.addWidget(self.vs_slider0_label)
        vbox_vs_slider0.addWidget(self.vs_slider0)
        hbox_vs.addLayout(vbox_vs_slider0)

        # Create the layout of the edit spacing controls
        hbox_edit = QtGui.QHBoxLayout()
        grid_edit = QtGui.QGridLayout()
        hline = create_hline()
        grid_edit.addWidget(hline, 0, 0, 1, 16)
        hline2 = create_hline()
        grid_edit.addWidget(hline2, 2, 0, 1, 16)
        vline = create_vline()
        grid_edit.addWidget(vline, 0, 0, 6, 1)
        label_active_finger_select = QtGui.QLabel('Active Finger Select')
        label_active_finger_select.setToolTip('Tools that select the active fingers')
        grid_edit.addWidget(label_active_finger_select, 1, 1, 1, 3, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_btn_toggle, 3, 1, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_btn_cursorL, 4, 1, QtCore.Qt.AlignRight)
        grid_edit.addWidget(self.edit_btn_cursorR, 4, 2, QtCore.Qt.AlignLeft)
        grid_edit.addWidget(self.edit_btn_activate_all, 3, 3)
        grid_edit.addWidget(self.edit_btn_deactivate_all, 4, 3)
        vline2 = create_vline()
        grid_edit.addWidget(vline2, 0, 4, 6, 1)
        label_active_finger_ops = QtGui.QLabel('Active Finger Operators')
        label_active_finger_ops.setToolTip('Edit operations applied to active fingers')
        grid_edit.addWidget(label_active_finger_ops, 1, 5, 1, 10, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_move_label, 3, 5, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_btn_moveL, 4, 5, QtCore.Qt.AlignRight)
        grid_edit.addWidget(self.edit_btn_moveR, 4, 6, QtCore.Qt.AlignLeft)
        vline3 = create_vline()
        grid_edit.addWidget(vline3, 2, 7, 4, 1)
        grid_edit.addWidget(self.edit_widen_label, 3, 8, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_btn_widenL, 4, 8, QtCore.Qt.AlignRight)
        grid_edit.addWidget(self.edit_btn_widenR, 4, 9, QtCore.Qt.AlignLeft)
        vline4 = create_vline()
        grid_edit.addWidget(vline4, 2, 10, 4, 1)
        grid_edit.addWidget(self.edit_trim_label, 3, 11, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(self.edit_btn_trimL, 4, 11, QtCore.Qt.AlignRight)
        grid_edit.addWidget(self.edit_btn_trimR, 4, 12, QtCore.Qt.AlignLeft)
        vline5 = create_vline()
        grid_edit.addWidget(vline5, 2, 13, 4, 1)
        grid_edit.addWidget(self.edit_btn_add, 3, 14)
        grid_edit.addWidget(self.edit_btn_del, 4, 14)
        vline6 = create_vline()
        grid_edit.addWidget(vline6, 0, 15, 6, 1)
        hline3 = create_hline()
        grid_edit.addWidget(hline3, 5, 0, 1, 16)
        grid_edit.setSpacing(5)

        hbox_edit.addLayout(grid_edit)
        hbox_edit.addStretch(1)
        hbox_edit.addWidget(self.edit_btn_undo)

        # Add the spacing layouts as Tabs
        self.tabs_spacing = QtGui.QTabWidget()
        tab_es = QtGui.QWidget()
        tab_es.setLayout(hbox_es)
        self.tabs_spacing.addTab(tab_es, 'Equal')
        tab_vs = QtGui.QWidget()
        tab_vs.setLayout(hbox_vs)
        self.tabs_spacing.addTab(tab_vs, 'Variable')
        tab_edit = QtGui.QWidget()
        tab_edit.setLayout(hbox_edit)
        self.tabs_spacing.addTab(tab_edit, 'Editor')
        self.tabs_spacing.currentChanged.connect(self._on_tabs_spacing)
        tip = 'These tabs specify the layout algorithm for the fingers.'
        self.tabs_spacing.setToolTip(tip)

        # The tab indices should be set in the order they're defined, but this ensures it
        self.equal_spacing_id = self.tabs_spacing.indexOf(tab_es)
        self.var_spacing_id = self.tabs_spacing.indexOf(tab_vs)
        self.edit_spacing_id = self.tabs_spacing.indexOf(tab_edit)
        # set default spacing tab to Equal
        self.spacing_index = self.equal_spacing_id
        self.tabs_spacing.setCurrentIndex(self.spacing_index)

        # either add the spacing Tabs to the bottom
        #vbox.addLayout(hbox)
        #vbox.addWidget(self.tabs_spacing)
        # ... or to the right of the text boxes
        hbox.addWidget(self.tabs_spacing)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
#        vbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        # Lay it all out
        self.main_frame.setLayout(vbox)
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
        if self.config.debug:
            print('draw')
        self.template = router.Incra_Template(self.units, self.board)
        self.fig.draw(self.template, self.board, self.bit, self.spacing)

    def reinit_spacing(self):
        '''
        Re-initializes the joint spacing objects.  This must be called
        when the router bit or board change dimensions.
        '''
        self.spacing_index = self.tabs_spacing.currentIndex()

        # Re-create the spacings objects
        if self.spacing_index == self.equal_spacing_id:
            self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board, self.config)
        elif self.spacing_index == self.var_spacing_id:
            self.var_spacing = spacing.Variable_Spaced(self.bit, self.board, self.config)
        elif self.spacing_index == self.edit_spacing_id:
            self.edit_spacing = spacing.Edit_Spaced(self.bit, self.board, self.config)
        else:
            raise ValueError('Bad value for spacing_index %d' % self.spacing_index)

        self.set_spacing_widgets()

    def set_spacing_widgets(self):
        '''
        Sets the spacing widget parameters
        '''
        # enable/disable editing of line edit boxes, depending upon spacing
        # algorithm
        tbs = [self.tb_board_width, self.tb_bit_width, self.tb_bit_depth,\
               self.tb_bit_angle]
        if self.spacing_index == self.edit_spacing_id:
            for tb in tbs:
                tb.setEnabled(False)
                tb.setStyleSheet("color: gray;")
        else:
            for tb in tbs:
                tb.setEnabled(True)
                tb.setStyleSheet("color: black;")

        if self.spacing_index == self.equal_spacing_id:
            # Equal spacing widgets
            params = self.equal_spacing.params
            p = params['B-spacing']
            self.es_slider0.blockSignals(True)
            self.es_slider0.setMinimum(p.vMin)
            self.es_slider0.setMaximum(p.vMax)
            self.es_slider0.setValue(p.v)
            self.es_slider0.blockSignals(False)
            p = params['Width']
            self.es_slider1.blockSignals(True)
            self.es_slider1.setMinimum(p.vMin)
            self.es_slider1.setMaximum(p.vMax)
            self.es_slider1.setValue(p.v)
            self.es_slider1.blockSignals(False)
            p = params['Centered']
            centered = p.v
            self.cb_es_centered.blockSignals(True)
            self.cb_es_centered.setChecked(centered)
            self.cb_es_centered.blockSignals(False)

            self.equal_spacing.set_cuts()
            self.es_slider0_label.setText(self.equal_spacing.labels[0])
            self.es_slider1_label.setText(self.equal_spacing.labels[1])
            self.spacing = self.equal_spacing
        elif self.spacing_index == self.var_spacing_id:
            # Variable spacing widgets
            params = self.var_spacing.params
            p = params['Fingers']
            self.vs_slider0.blockSignals(True)
            self.vs_slider0.setMinimum(p.vMin)
            self.vs_slider0.setMaximum(p.vMax)
            self.vs_slider0.setValue(p.v)
            self.vs_slider0.blockSignals(False)
            self.var_spacing.set_cuts()
            self.vs_slider0_label.setText(self.var_spacing.labels[0])
            self.spacing = self.var_spacing
        elif self.spacing_index == self.edit_spacing_id:
            # Edit spacing parameters.  Currently, this has no parameters, and
            # uses as a starting spacing whatever the previous spacing set.
            self.edit_spacing.set_cuts(self.spacing.cuts)
            self.spacing = self.edit_spacing
        else:
            raise ValueError('Bad value for spacing_index %d' % self.spacing_index)

    @QtCore.pyqtSlot(int)
    def _on_tabs_spacing(self, index):
        '''Handles changes to spacing algorithm'''
        if self.config.debug:
            print('_on_tabs_spacing')
        if self.spacing_index == self.edit_spacing and index != self.edit_spacing and \
                    self.spacing.changes_made():
            msg = 'You are exiting the Editor, which will discard'\
                  ' any changes made in the Editor.'\
                  '\n\nAre you sure you want to do this?'
            reply = QtGui.QMessageBox.question(self, 'Message', msg,
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                self.tabs_spacing.setCurrentIndex(self.spacing_index)
                return
        self.reinit_spacing()
        self.draw()
        self.status_message('Changed to spacing algorithm %s'\
                            % str(self.tabs_spacing.tabText(index)))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_width(self):
        '''Handles changes to bit width'''
        if self.config.debug:
            print('_on_bit_width')
        # With editingFinished, we also need to check whether the
        # value actually changed. This is because editingFinished gets
        # triggered every time focus changes, which can occur many
        # times when an exception is thrown, or user tries to quit
        # in the middle of an exception, etc.  This logic also avoids
        # unnecessary redraws.
        if self.tb_bit_width.isModified():
            if self.config.debug:
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
        if self.config.debug:
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
        if self.config.debug:
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
        if self.config.debug:
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
        if self.config.debug:
            print('_on_es_slider0', value)
        self.equal_spacing.params['B-spacing'].v = value
        self.equal_spacing.set_cuts()
        self.es_slider0_label.setText(self.equal_spacing.labels[0])
        self.draw()
        self.status_message('Changed slider %s' % str(self.es_slider0_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_es_slider1(self, value):
        '''Handles changes to the equally-spaced slider Width'''
        if self.config.debug:
            print('_on_es_slider1', value)
        self.equal_spacing.params['Width'].v = value
        self.equal_spacing.set_cuts()
        self.es_slider1_label.setText(self.equal_spacing.labels[1])
        self.draw()
        self.status_message('Changed slider %s' % str(self.es_slider1_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_cb_es_centered(self):
        '''Handles changes to centered checkbox'''
        if self.config.debug:
            print('_on_cb_es_centered')
        self.equal_spacing.params['Centered'].v = self.cb_es_centered.isChecked()
        self.equal_spacing.set_cuts()
        self.draw()
        if self.equal_spacing.params['Centered'].v:
            self.status_message('Checked Centered.')
        else:
            self.status_message('Unchecked Centered.')
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_vs_slider0(self, value):
        '''Handles changes to the variable-spaced slider Fingers'''
        if self.config.debug:
            print('_on_vs_slider0', value)
        self.var_spacing.params['Fingers'].v = value
        self.var_spacing.set_cuts()
        self.vs_slider0_label.setText(self.var_spacing.labels[0])
        self.draw()
        self.status_message('Changed slider %s' % str(self.vs_slider0_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_screenshot(self):
        '''
        Handles screenshot events.
        '''
        if self.config.debug:
            print('_on_screenshot')
        self._on_save(True)

    @QtCore.pyqtSlot()
    def _on_save(self, do_screenshot=False):
        '''
        Handles save file events. The file format is PNG, with metadata
        to support recreating the joint.
        '''
        if self.config.debug:
            print('_on_save')

        # Get the file name.  The default name is indexed on the number
        # of times this function is called.
        defname = os.path.join(self.working_dir,
                               'screenshot_%d.png' % (self.screenshot_index))

        # This is the simple approach to set the filename, but doesn't allow
        # us to update the working_dir, if the user changes it.
        #filename = QtGui.QFileDialog.getSaveFileName(self, 'Save file', \
        #                                             defname, 'Portable Network Graphics (*.png)')
        # ... so here is now we do it:
        dialog = QtGui.QFileDialog(self, 'Save file', defname, \
                                   'Portable Network Graphics (*.png)')
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        filename = None
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            self.working_dir = str(dialog.directory().path())
            filename = str(filenames[0]).strip()
        if filename is None:
            self.status_message('File not saved')
            return

        # Save the file with metadata
        if do_screenshot:
            image = QtGui.QPixmap.grabWindow(self.winId()).toImage()
        else:
            image = self.fig.image(self.template, self.board, self.bit, self.spacing)

        s = serialize.serialize(self.bit, self.board, self.spacing, \
                                self.config.debug)
        image.setText('pyRouterJig', s)
        r = image.save(filename, 'png')
        if r:
            self.status_message('Saved to file %s' % filename)
            self.screenshot_index += 1
            self.file_saved = True
        else:
            self.status_message('Unable to save to file %s' % filename)

    @QtCore.pyqtSlot()
    def _on_open(self):
        '''
        Handles open file events.  The file format is  PNG, with metadata
        to support recreating the joint.  In other words, the file must
        have been saved using _on_save().
        '''
        if self.config.debug:
            print('_on_open')

        # Make sure changes are not lost
        if not self.file_saved:
            msg = 'Current joint not saved.'\
                  ' Opening a new file will overwrite the current joint.'\
                  '\n\nAre you sure you want to do this?'
            reply = QtGui.QMessageBox.question(self, 'Message', msg,
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                return

        # Get the file name
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', \
                                                     self.working_dir, \
                                                     'Portable Network Graphics (*.png)')
        filename = str(filename).strip()
        if len(filename) == 0:
            self.status_message('File open aborted')
            return

        # From the image file, parse the metadata.  Maintain the board icon
        # from its current value, rather than reading it from the file.
        image = QtGui.QImage(filename)
        s = image.text('pyRouterJig') # see setText in _on_save
        if len(s) == 0:
            msg = 'File %s does not contain pyRouterJig data.  The PNG file'\
                  ' must have been saved using pyRouterJig.' % filename
            QtGui.QMessageBox.warning(self, 'Error', msg)
            return
        icon = self.board.icon
        (self.bit, self.board, sp, sp_type) = serialize.unserialize(s, self.config.debug)
        self.board.set_icon(icon)

        # Reset the dependent data
        self.units = self.bit.units
        self.template = router.Incra_Template(self.units, self.board)
        if sp_type == 'Equa':
            sp.set_cuts()
            self.equal_spacing = sp
            self.spacing_index = self.equal_spacing_id
        elif sp_type == 'Vari':
            sp.set_cuts()
            self.var_spacing = sp
            self.spacing_index = self.var_spacing_id
        elif sp_type == 'Edit':
            self.edit_spacing = sp
            self.spacing_index = self.edit_spacing_id
        self.spacing = sp
        self.tabs_spacing.blockSignals(True)
        self.tabs_spacing.setCurrentIndex(self.spacing_index)
        self.tabs_spacing.blockSignals(False)
        self.tb_board_width.setText(self.units.increments_to_string(self.board.width))
        self.tb_bit_width.setText(self.units.increments_to_string(self.bit.width))
        self.tb_bit_depth.setText(self.units.increments_to_string(self.bit.depth))
        self.tb_bit_angle.setText(`self.bit.angle`)
        self.set_spacing_widgets()
        self.draw()

    @QtCore.pyqtSlot()
    def _on_print(self):
        '''Handles print events'''
        if self.config.debug:
            print('_on_print')

        r = self.fig.print(self.template, self.board, self.bit, self.spacing)
        if r:
            self.status_message('Figure printed')
        else:
            self.status_message('Figure not printed')

    @QtCore.pyqtSlot()
    def _on_exit(self):
        '''Handles code exit events'''
        if self.config.debug:
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
        if self.config.debug:
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
        if self.config.debug:
            print('_on_doclink')

        webbrowser.open('http://lowrie.github.io/pyRouterJig/documentation.html')

    @QtCore.pyqtSlot()
    def _on_units(self):
        '''Handles changes in units'''
        if self.config.debug:
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
        self.tb_board_width.setText(self.units.increments_to_string(self.board.width))
        self.tb_bit_width.setText(self.units.increments_to_string(self.bit.width))
        self.tb_bit_depth.setText(self.units.increments_to_string(self.bit.depth))
        self.reinit_spacing()
        self.update_tooltips()
        self.draw()

    @QtCore.pyqtSlot()
    def _on_wood(self):
        '''Handles changes in wood'''
        if self.config.debug:
            print('_on_wood')
        for k, v in self.wood_actions.items():
            if v.isChecked():
                wood = k
                break
        self.board.set_icon(self.woods[wood])
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_undo(self):
        '''Handles undo event'''
        if self.config.debug:
            print('_on_edit_undo')
        self.spacing.undo()
        self.statusbar.showMessage('Undo')
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_moveL(self):
        '''Handles move left event'''
        if self.config.debug:
            print('_on_edit_moveL')
        msg = self.spacing.finger_move_left()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_moveR(self):
        '''Handles move right event'''
        if self.config.debug:
            print('_on_edit_moveR')
        msg = self.spacing.finger_move_right()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_widenL(self):
        '''Handles widen left event'''
        if self.config.debug:
            print('_on_edit_widenL')
        msg = self.spacing.finger_widen_left()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_widenR(self):
        '''Handles widen right event'''
        if self.config.debug:
            print('_on_edit_widenR')
        msg = self.spacing.finger_widen_right()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_trimL(self):
        '''Handles trim left event'''
        if self.config.debug:
            print('_on_edit_trimL')
        msg = self.spacing.finger_trim_left()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_trimR(self):
        '''Handles trim right event'''
        if self.config.debug:
            print('_on_edit_trimR')
        msg = self.spacing.finger_trim_right()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_toggle(self):
        '''Handles edit toggle event'''
        if self.config.debug:
            print('_on_edit_toggle')
        msg = self.spacing.finger_toggle()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_cursorL(self):
        '''Handles cursor left event'''
        if self.config.debug:
            print('_on_edit_cursorL')
        msg = self.spacing.finger_increment_cursor(-1)
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_cursorR(self):
        '''Handles toggle right event'''
        if self.config.debug:
            print('_on_edit_cursorR')
        msg = self.spacing.finger_increment_cursor(1)
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_activate_all(self):
        '''Handles edit activate all event'''
        if self.config.debug:
            print('_on_edit_activate_all')
        msg = self.spacing.finger_all_active()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_deactivate_all(self):
        '''Handles edit deactivate all event'''
        if self.config.debug:
            print('_on_edit_deactivate_all')
        msg = self.spacing.finger_all_not_active()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_add(self):
        '''Handles add finger event'''
        if self.config.debug:
            print('_on_edit_add')
        msg = self.spacing.finger_add()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_del(self):
        '''Handles delete fingers event'''
        if self.config.debug:
            print('_on_edit_del')
        msg = self.spacing.finger_delete_active()
        self.statusbar.showMessage(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_flash_status_off(self):
        '''Handles event to turn off statusbar message'''
        if self.config.debug:
            print('_on_flash_status_off')
        self.statusbar.showMessage('')

    def status_message(self, msg, flash_len_ms=None):
        '''Flashes a status message to the status bar'''
        self.statusbar.showMessage(msg)
        if flash_len_ms is not None:
            QtCore.QTimer.singleShot(flash_len_ms, self._on_flash_status_off)

    def closeEvent(self, event):
        '''
        For closeEvents (user closes window or presses Ctrl-Q), ignore and call
        _on_exit()
        '''
        if self.config.debug:
            print('closeEvent')
        self._on_exit()
        event.ignore()

    def keyPressEvent(self, event):
        '''
        Handles key press events
        '''
        # return if not edit spacing
        if self.tabs_spacing.currentIndex() != self.edit_spacing_id:
            event.ignore()
            return

        msg = None
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = True
        elif event.key() == QtCore.Qt.Key_Control:
            self.control_key = True
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = True
        elif event.key() == QtCore.Qt.Key_U:
            self.spacing.undo()
            msg = 'Undo'
            self.draw()
        elif event.key() == QtCore.Qt.Key_A:
            msg = self.spacing.finger_all_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_N:
            msg = self.spacing.finger_all_not_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Return:
            msg = self.spacing.finger_toggle()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Minus:
            msg = self.spacing.finger_delete_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Plus:
            msg = self.spacing.finger_add()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Left:
            if self.shift_key:
                msg = self.spacing.finger_widen_left()
            elif self.control_key:
                msg = self.spacing.finger_trim_left()
            elif self.alt_key:
                msg = self.spacing.finger_move_left()
            else:
                msg = self.spacing.finger_increment_cursor(-1)
            self.draw()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.shift_key:
                msg = self.spacing.finger_widen_right()
            elif self.control_key:
                msg = self.spacing.finger_trim_right()
            elif self.alt_key:
                msg = self.spacing.finger_move_right()
            else:
                msg = self.spacing.finger_increment_cursor(1)
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
        if self.tabs_spacing.currentIndex() != self.edit_spacing_id:
            event.ignore()
            return

        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = False
        elif event.key() == QtCore.Qt.Key_Control:
            self.control_key = False
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = False
        else:
            if self.config.debug:
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
