###########################################################################
#
# Copyright 2015-2018 Robert B. Lowrie (http://github.com/lowrie)
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

import os
import platform
import sys
import traceback
import webbrowser
import copy
import shutil
from io import BytesIO
from decimal import getcontext
from builtins import str
from PIL import Image
if platform.system() != 'Darwin':
    from PIL import ImageCms
from PIL import PngImagePlugin
from PyQt5 import QtCore, QtGui, QtWidgets
import qt_fig
import qt_config
import qt_utils
import config_file
import router
import spacing
import utils
import doc
import serialize
import threeDS


class Driver(QtWidgets.QMainWindow):
    '''
    Qt driver for pyRouterJig
    '''
    def __init__(self, parent=None, app=None):

        QtWidgets.QMainWindow.__init__(self, parent)
        sys.excepthook = self.exception_hook
        self.except_handled = False

        # translator initialized in load config but we need the object created first
        self.transl = QtCore.QTranslator()

        # Read the config file.  We wait until the end of this init to print
        # the status message, because we need the statusbar to be created first.
        (self.config, msg) = self.load_config(app)

        # Form the units
        self.units = utils.Units(self.config.english_separator, self.config.metric,
                                 self.config.num_increments, self.transl)
        self.doc = doc.Doc(self.units)

        # Create an initial joint.  Even though another joint may be opened
        # later, we do this now so that the initial widget layout may be
        # created.
        bit_width = self.units.abstract_to_increments(self.config.bit_width)
        bit_depth = self.units.abstract_to_increments(self.config.bit_depth)
        bit_angle = self.units.abstract_to_float(self.config.bit_angle)
        bit_gentle = self.config.bit_gentle
        self.bit = router.Router_Bit(self.units, bit_width, bit_depth, bit_angle, bit_gentle)
        self.boards = []
        board_width = self.units.abstract_to_increments(self.config.board_width)

        for _ in range(4):
            self.boards.append(router.Board(self.bit, width=board_width))
        self.boards[2].set_active(False)
        self.boards[3].set_active(False)
        dbt = self.units.abstract_to_increments(self.config.double_board_thickness)
        self.boards[2].set_height(self.bit, dbt)
        self.boards[3].set_height(self.bit, dbt)
        self.template = router.Incra_Template(self.units, self.boards)
        self.equal_spacing = spacing.Equally_Spaced(self.bit, self.boards, self.config)
        self.equal_spacing.set_cuts()
        self.var_spacing = spacing.Variable_Spaced(self.bit, self.boards, self.config)
        self.var_spacing.set_cuts()
        self.edit_spacing = spacing.Edit_Spaced(self.bit, self.boards, self.config)
        self.edit_spacing.set_cuts(self.equal_spacing.cuts)
        self.spacing = self.equal_spacing  # the default
        self.spacing_index = None  # to be set in layout_widgets()
        self.description = None
        self.woods = {}

        # Create the main frame and menus
        self.create_status_bar()
        self.create_widgets()
        self.create_menu()

        # Draw the initial figure
        self.draw()

        # Keep track whether the current figure has been saved.  We initialize to true,
        # because we assume that that the user does not want the default joint saved.
        self.file_saved = True

        # The working_dir is where we save files.  We start with the user home
        # directory.  Ideally, if using the script to start the program, then
        # we'd use the cwd, but that's complicated.
        self.working_dir = os.path.expanduser('~')

        # Indices for screenshot/save and table filenames
        self.screenshot_index = None
        self.table_index = None

        # Initialize keyboard modifiers
        self.control_key = False
        self.alt_key = False

        # Initialize the configuration window, even though we might not use
        # it.  We do this so that if certain preferences are changed via the
        # menus, such as show_caul, the config window keeps track whether any such
        # changes have occurred, in order to enable its Save button.
        self.config_window = qt_config.Config_Window(self.config, self.units, self)
        (self.working_dir, fname) = os.path.split(os.path.splitext(self.config.last_path)[0])
        self.prefix = fname.rstrip('0123456789')

        # ... show the status message from reading the configuration file
        self.status_message(msg)

    def load_config(self, app=None):
        '''
        Sets the config attribute, by either
           1) Reading an existing config file
           2) Updating an existing config file and loading it
           3) Creating the config file, if it does not exist
        '''
        c = config_file.Configuration()
        r = c.read_config()

        locale = QtCore.QLocale()
        if r != 1 and getattr(c.config, "language", None) != None:
            locale = QtCore.QLocale(c.config.language)

        res = self.transl.load("pyRouterJig_%s.qm" % locale.name(), ".\\ts")
        if res and app != None:
            app.installTranslator(self.transl)

        if r > 0:
            tools = 'Tools'
            if utils.isMac():
                tools = 'pyRouterJig'
            if r == 1:
                # The config file does not exist.  Ask the user whether they want metric or english
                # units
                box = QtWidgets.QMessageBox(self)
                box.setTextFormat(QtCore.Qt.RichText)
                box.setIcon(QtWidgets.QMessageBox.NoIcon)
                box.setText(self.transl.tr(
                    '<font size=5 color=red>Welcome to <i>pyRouterJig</i> !</font>'))
                question = self.transl.tr('<font size=5>Please select a unit system below.'\
                           ' The configuration file<p><tt>{}</tt><p>'\
                           ' will be created to store this setting,'\
                           ' along with additional default settings.  These options'\
                           ' may be changed later by selecting <b>Preferences</b> under'\
                           ' the <b>{}</b> menu.</font>').format(c.filename, tools)
                box.setInformativeText(question)
                buttonMetric = box.addButton(self.transl.tr('Metric (millimeters)'),
                                             QtWidgets.QMessageBox.AcceptRole)
                buttonEnglish = box.addButton(self.transl.tr('English (inches)'),
                                              QtWidgets.QMessageBox.AcceptRole)
                box.setDefaultButton(buttonEnglish)
                box.raise_()
                box.exec_()
                clicked = box.clickedButton()
                metric = (clicked == buttonMetric)
                c.create_config(metric)
            else:  # r == 2
                # The config file exists, but it's out of date, so
                # update it.  Tell the user and use the old metric setting.
                backup = c.filename + c.config.version
                shutil.move(c.filename, backup)
                metric = c.config.metric
                rc = c.create_config(metric)
                box = QtWidgets.QMessageBox(self)
                box.setTextFormat(QtCore.Qt.RichText)
                box.setIcon(QtWidgets.QMessageBox.Warning)
                box.setText(self.transl.tr(
                    '<font size=5 color=red>Welcome to <i>pyRouterJig</i> !'))
                warning = self.transl.tr('<font size=5>A new configuration file<p><tt>{}</tt><p>'\
                          'has been created. The old version was saved'\
                          ' to<p><tt>{}</tt><p> ').format(c.filename, backup)
                if rc == 0:
                    warning += self.transl.tr('The previous setting of'\
                               '<p><i>metric = {}</i><p>has been migrated.'\
                               ' But any other changes that you may have made'\
                               ' to the old file will need to be migrated to the'\
                               ' new file, or by selecting <b>Preferences</b>'\
                               ' under the <b>{}</b> menu.').format(metric, tools)
                else:
                    warning += self.transl.tr('The old configuration values were migrated'\
                                              ' and any new values were set to their default.')
                box.setInformativeText(warning)
                box.raise_()
                box.exec_()
                self.raise_()
            msg = 'Configuration file %s created' % c.filename
            c.read_config()
        else:
            # The config file exists and is current
            msg = self.transl.tr('Read configuration file %s') % c.filename

        self.setWindowTitle('pyRouterJig ' + c.config.version)
        return (c.config, msg)

    def center(self):
        '''Centers the app in the screen'''
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(
            QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def exception_hook(self, etype, value, trace):
        '''
        Handler for all exceptions.
        '''
        if self.except_handled:
            return

        self.except_handled = True
        if self.config.debug:
            tmp = traceback.format_exception(etype, value, trace)
            traceback.print_tb(trace)
        else:
            tmp = traceback.format_exception_only(etype, value)
        exception = '\n'.join(tmp)

        QtWidgets.QMessageBox.warning(self, 'Error', exception)
        self.except_handled = False

    def create_menu(self):
        '''
        Creates the drop-down menus.
        '''
        self.menubar = self.menuBar()

        # always attach the menubar to the application window, even on the Mac
        # self.menubar.setNativeMenuBar(False)

        # Add the file menu

        file_menu = self.menubar.addMenu(self.transl.tr('File'))

        open_action = QtWidgets.QAction(self.transl.tr('&Open File...'), self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip(self.transl.tr('Opens a previously saved image of joint'))
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QtWidgets.QAction(self.transl.tr('&Save File...'), self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip(self.transl.tr('Saves an image of the joint to a file'))
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        print_action = QtWidgets.QAction(self.transl.tr('&Print...'), self)
        print_action.setShortcut('Ctrl+P')
        print_action.setStatusTip(self.transl.tr('Print the figure'))
        print_action.triggered.connect(self._on_print)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction(self.transl.tr('&Quit pyRouterJig'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip(self.transl.tr('Quit pyRouterJig'))
        exit_action.triggered.connect(self._on_exit)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # comment out for now...
        # table_action = QtWidgets.QAction('Print Table...', self)
        # table_action.setStatusTip('Print a table of router pass locations')
        # table_action.triggered.connect(self._on_print_table)
        # file_menu.addAction(table_action)

        # Add view menu

        view_menu = self.menubar.addMenu(self.transl.tr('View'))

        self.caul_action = QtWidgets.QAction(self.transl.tr('Caul Template'), self, checkable=True)
        self.caul_action.setStatusTip(self.transl.tr('Toggle caul template'))
        self.caul_action.triggered.connect(self._on_caul)
        view_menu.addAction(self.caul_action)
        self.caul_action.setChecked(self.config.show_caul)

        self.finger_size_action = QtWidgets.QAction(self.transl.tr('Finger Widths'),
                                                    self, checkable=True)
        self.finger_size_action.setStatusTip(self.transl.tr('Toggle viewing finger sizes'))
        self.finger_size_action.triggered.connect(self._on_finger_sizes)
        view_menu.addAction(self.finger_size_action)
        self.finger_size_action.setChecked(self.config.show_finger_widths)

        self.fit_action = QtWidgets.QAction(self.transl.tr('Fit'), self, checkable=True)
        self.fit_action.setStatusTip(self.transl.tr('Toggle showing fit of joint'))
        self.fit_action.triggered.connect(self._on_fit)
        view_menu.addAction(self.fit_action)
        self.fit_action.setChecked(self.config.show_fit)

        self.zoom_action = QtWidgets.QAction(self.transl.tr('Zoom Mode'), self, checkable=True)
        self.zoom_action.setStatusTip(self.transl.tr('Toggle zoom mode'))
        self.zoom_action.triggered.connect(self._on_zoom)
        view_menu.addAction(self.zoom_action)
        self.fig.enable_zoom_mode(False)
        self.fit_action.setChecked(self.fig.zoom_mode)

        view_menu.addSeparator()

        pass_menu = view_menu.addMenu(self.transl.tr('Router Passes'))
        self.pass_id_action = QtWidgets.QAction(self.transl.tr('Identifiers'), self, checkable=True)
        self.pass_id_action.setStatusTip(self.transl.tr('Toggle viewing router pass identifiers'))
        self.pass_id_action.triggered.connect(self._on_pass_id)
        pass_menu.addAction(self.pass_id_action)
        self.pass_id_action.setChecked(self.config.show_router_pass_identifiers)

        self.pass_location_action = QtWidgets.QAction(self.transl.tr('Locations'),
                                                      self, checkable=True)
        self.pass_location_action.setStatusTip(self.transl.tr(
            'Toggle viewing router pass locations'))
        self.pass_location_action.triggered.connect(self._on_pass_location)
        pass_menu.addAction(self.pass_location_action)
        self.pass_location_action.setChecked(self.config.show_router_pass_locations)

        # The Mac automatically adds full screen to the View menu, but do so for other platforms
        # if not utils.isMac():
        view_menu.addSeparator()
        fullscreen_action = QtWidgets.QAction(self.transl.tr('Full Screen Mode'),
                                              self, checkable=True)
        fullscreen_action.setShortcut('Ctrl+F')
        fullscreen_action.setStatusTip(self.transl.tr('Toggle full-screen mode'))
        fullscreen_action.triggered.connect(self._on_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Add Tools menu

        tools_menu = self.menubar.addMenu(self.transl.tr('Tools'))

        screenshot_action = QtWidgets.QAction(self.transl.tr('Screenshot...'), self)
        screenshot_action.setShortcut('Ctrl+W')
        screenshot_action.setStatusTip(self.transl.tr(
            'Saves an image of the pyRouterJig window to a file'))
        screenshot_action.triggered.connect(self._on_screenshot)
        tools_menu.addAction(screenshot_action)

        # We need to make this action persistent, so that we can
        # enable and disable it (until all of its functionality is
        # written)
        self.threeDS_action = QtWidgets.QAction(self.transl.tr('&Export 3DS...'), self)
        self.threeDS_action.setShortcut('Ctrl+E')
        self.threeDS_action.setStatusTip(self.transl.tr('Export the joint to a 3DS file'))
        self.threeDS_action.triggered.connect(self._on_3ds)
        tools_menu.addAction(self.threeDS_action)
        self.threeDS_enabler()

        tools_menu.addSeparator()

        pref_action = QtWidgets.QAction(self.transl.tr('Preferences...'), self)
        pref_action.setShortcut('Ctrl+,')
        pref_action.setStatusTip(self.transl.tr('Open preferences'))
        pref_action.triggered.connect(self._on_preferences)
        tools_menu.addAction(pref_action)

        # Add the help menu

        help_menu = self.menubar.addMenu(self.transl.tr('Help'))

        about_action = QtWidgets.QAction(self.transl.tr('&About pyRouterJig'), self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip(self.transl.tr('About this program'))
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

        view_menu.addSeparator()

        doclink_action = QtWidgets.QAction(self.transl.tr('&Documentation...'), self)
        doclink_action.setStatusTip(self.transl.tr('Opens documentation page in web browser'))
        doclink_action.triggered.connect(self._on_doclink)
        help_menu.addAction(doclink_action)

    def create_wood_combo_box(self, woods, patterns, has_none=False):
        '''
        Creates a wood selection combox box
        '''
        cb = qt_utils.PreviewComboBox(self)
        # Set the default wood.
        if has_none:
            # If adding NONE, make that the default
            defwood = 'NONE'
        else:
            defwood = QtCore.Qt.DiagCrossPattern
            if self.config.default_wood in self.woods.values():
                defwood = self.config.default_wood
        self.populate_wood_combo_box(cb, woods, patterns, defwood, has_none)
        # Don't let the user change the text for each selection
        cb.setEditable(False)
        return cb

    def populate_wood_combo_box(self, cb, woods, patterns, defwood, has_none):
        '''
        Fills the wood combo box
        '''
        cb.blockSignals(True)
        cb.clear()
        if has_none:
            cb.addItem('NONE')
        # Add the woods in the wood_images directory
        skeys = sorted(woods.keys())

        #combo boxes now store values as well as keys
        for k in skeys:
            cb.addItem(k, woods.get(k))
        # Next add patterns
        if skeys:
            cb.insertSeparator(len(skeys))
        skeys = sorted(patterns.keys())
        for k in skeys:
            cb.addItem(k, patterns.get(k))
        # Set the index to the default wood
        i = max(0, cb.findData(defwood))
        cb.setCurrentIndex(i)
        cb.blockSignals(False)

    def create_widgets(self):
        '''
        Creates all of the widgets in the main panel
        '''
        self.main_frame = QtWidgets.QWidget()

        lineEditWidth = 80
        us = self.units.units_string(withParens=True)

        # Create the figure canvas, using mpl interface
        self.fig = qt_fig.Qt_Fig(self.template, self.boards, self.config)
        self.fig.canvas.setParent(self.main_frame)
        self.fig.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.fig.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Expanding)
        self.fig.canvas.setFocus()

        # Board width line edit
        self.le_board_width_label = QtWidgets.QLabel(self.transl.tr('Board Width{}').format(us))
        self.le_board_width = QtWidgets.QLineEdit(self.main_frame)
        self.le_board_width.setFixedWidth(lineEditWidth)
        self.le_board_width.setText(self.units.increments_to_string(self.boards[0].width))
        self.le_board_width.editingFinished.connect(self._on_board_width)
        self.le_board_width.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Bit width line edit
        self.le_bit_width_label = QtWidgets.QLabel(self.transl.tr('Bit Width{}').format(us))
        self.le_bit_width = QtWidgets.QLineEdit(self.main_frame)
        self.le_bit_width.setFixedWidth(lineEditWidth)
        self.le_bit_width.setText(self.units.increments_to_string(self.bit.width))
        self.le_bit_width.editingFinished.connect(self._on_bit_width)

        # Bit depth line edit
        self.le_bit_depth_label = QtWidgets.QLabel(self.transl.tr('Bit Depth{}').format(us))
        self.le_bit_depth = QtWidgets.QLineEdit(self.main_frame)
        self.le_bit_depth.setFixedWidth(lineEditWidth)
        self.le_bit_depth.setText(self.units.increments_to_string(self.bit.depth))
        self.le_bit_depth.editingFinished.connect(self._on_bit_depth)

        # Bit angle line edit
        self.le_bit_angle_label = QtWidgets.QLabel(self.transl.tr('Bit Angle (deg.)'))
        self.le_bit_angle = QtWidgets.QLineEdit(self.main_frame)
        self.le_bit_angle.setFixedWidth(lineEditWidth)
        self.le_bit_angle.setText('%g' % self.bit.angle)
        self.le_bit_angle.editingFinished.connect(self._on_bit_angle)

        # Double and double-double board thicknesses
        self.le_boardm_label = []
        self.le_boardm = []
        for i in range(2):
            self.le_boardm_label.append(QtWidgets.QLabel(self.transl.tr('Thickness{}').format(us)))
            self.le_boardm.append(QtWidgets.QLineEdit(self.main_frame))
            self.le_boardm[i].setFixedWidth(lineEditWidth)
            s = self.units.increments_to_string(self.boards[i+2].dheight)
            self.le_boardm[i].setText(s)
        self.le_boardm[0].editingFinished.connect(self._on_boardm0)
        self.le_boardm[1].editingFinished.connect(self._on_boardm1)

        # Wood combo boxes
        (woods, patterns) = qt_utils.create_wood_dict(self.config.wood_images, self.transl)
        # ... combine the wood images and patterns
        self.woods = copy.deepcopy(woods)
        self.woods.update(patterns)
        # ... create the combo boxes and their labels
        self.cb_wood = []
        self.cb_wood.append(self.create_wood_combo_box(woods, patterns))
        self.cb_wood.append(self.create_wood_combo_box(woods, patterns))
        self.cb_wood.append(self.create_wood_combo_box(woods, patterns, True))
        self.cb_wood.append(self.create_wood_combo_box(woods, patterns, True))
        self.cb_wood_label = []
        self.cb_wood_label.append(QtWidgets.QLabel(self.transl.tr('Top Board')))
        self.cb_wood_label.append(QtWidgets.QLabel(self.transl.tr('Bottom Board')))
        self.cb_wood_label.append(QtWidgets.QLabel(self.transl.tr('Double Board')))
        self.cb_wood_label.append(QtWidgets.QLabel(self.transl.tr('Double-Double Board')))

        # Disable double* boards, for now
        self.le_boardm[0].setEnabled(False)
        self.le_boardm[1].setEnabled(False)
        self.le_boardm[0].setStyleSheet("color: gray;")
        self.le_boardm[1].setStyleSheet("color: gray;")
        self.le_boardm_label[0].setStyleSheet("color: gray;")
        self.le_boardm_label[1].setStyleSheet("color: gray;")
        self.cb_wood[3].setEnabled(False)
        self.cb_wood_label[3].setStyleSheet("color: gray;")

        # Equal spacing widgets

        params = self.equal_spacing.params
        labels = self.equal_spacing.labels

        # ...first slider
        p = params['Spacing']
        self.es_slider0_label = QtWidgets.QLabel(labels[0])
        self.es_slider0 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider0.setMinimum(p.vMin)
        self.es_slider0.setMaximum(p.vMax)
        self.es_slider0.setValue(p.v)
        self.es_slider0.setTickPosition(QtWidgets.QSlider.TicksBelow)
        utils.set_slider_tick_interval(self.es_slider0)
        self.es_slider0.valueChanged.connect(self._on_es_slider0)
        self.es_slider0.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # ...second slider
        p = params['Width']
        self.es_slider1_label = QtWidgets.QLabel(labels[1])
        self.es_slider1 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider1.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider1.setMinimum(p.vMin)
        self.es_slider1.setMaximum(p.vMax)
        self.es_slider1.setValue(p.v)
        self.es_slider1.setTickPosition(QtWidgets.QSlider.TicksBelow)
        utils.set_slider_tick_interval(self.es_slider1)
        self.es_slider1.valueChanged.connect(self._on_es_slider1)
        self.es_slider1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # ...check box for centering
        p = params['Centered']
        self.cb_es_centered = QtWidgets.QCheckBox(labels[2], self.main_frame)
        self.cb_es_centered.setChecked(True)
        self.cb_es_centered.stateChanged.connect(self._on_cb_es_centered)

        # Variable spacing widgets

        params = self.var_spacing.params
        labels = self.var_spacing.labels

        # ...combox box for fingers
        p = params['Fingers']
        self.cb_vsfingers_label = QtWidgets.QLabel(labels[0]) # labels[0]
        self.cb_vsfingers = qt_utils.PreviewComboBox(self.main_frame)
        self.cb_vsfingers.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.update_cb_vsfingers(p.vMin, p.vMax, p.v)

        p = params['Spacing']
        self.vs_slider0_label = QtWidgets.QLabel(self.transl.tr('Spacing...'), self.main_frame) # labels[1]
        self.vs_slider0 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.vs_slider0.setToolTip(self.transl.tr('Set fingers disstance'))
        self.vs_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.v)
        self.vs_slider0.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.vs_slider0.setSingleStep(1)
        utils.set_slider_tick_interval(self.vs_slider0)
        self.vs_slider0.valueChanged.connect(self._on_vs_slider0)
        self.vs_slider0.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # line out lables (haveno idea why
        width = (self.vs_slider0_label.width())
        self.cb_vsfingers_label.setFixedWidth(width // 2)
        height = (self.vs_slider0_label.height())
        self.vs_slider0_label.setFixedHeight((height * 10) // 8)
        self.cb_vsfingers_label.setFixedHeight((height * 8) // 10)
        # self.vs_slider0.setFixedHeight(self.cb_vsfingers.height())

        # ...check box for centering
        p = params['Inverted']
        self.cb_vs_inverted = QtWidgets.QCheckBox(self.transl.tr('Inverted'), self.main_frame) # labels[2]
        self.cb_vs_inverted.setToolTip(self.transl.tr('Inverce pattern'))
        self.cb_vs_inverted.setChecked(p.v)
        self.cb_vs_inverted.stateChanged.connect(self._cb_vs_inverted)

        # Edit spacing widgets

        edit_btn_undo = QtWidgets.QPushButton(self.transl.tr('Undo'), self.main_frame)
        edit_btn_undo.clicked.connect(self._on_edit_undo)
        edit_btn_undo.setToolTip(self.transl.tr('Undo the last change'))
        edit_btn_add = QtWidgets.QPushButton(self.transl.tr('Add'), self.main_frame)
        edit_btn_add.clicked.connect(self._on_edit_add)
        edit_btn_add.setToolTip(self.transl.tr('Add a cut (if there is space to add cuts)'))
        edit_btn_del = QtWidgets.QPushButton(self.transl.tr('Delete'), self.main_frame)
        edit_btn_del.clicked.connect(self._on_edit_del)
        edit_btn_del.setToolTip(self.transl.tr('Delete the active cuts'))

        edit_move_label = QtWidgets.QLabel(self.transl.tr('Move'))
        edit_move_label.setToolTip(self.transl.tr('Moves the active cuts'))
        edit_btn_moveL = QtWidgets.QToolButton(self.main_frame)
        edit_btn_moveL.setArrowType(QtCore.Qt.LeftArrow)
        edit_btn_moveL.clicked.connect(self._on_edit_moveL)
        edit_btn_moveL.setToolTip(self.transl.tr('Move active cuts to left 1 increment'))
        edit_btn_moveR = QtWidgets.QToolButton(self.main_frame)
        edit_btn_moveR.setArrowType(QtCore.Qt.RightArrow)
        edit_btn_moveR.clicked.connect(self._on_edit_moveR)
        edit_btn_moveR.setToolTip(self.transl.tr('Move active cuts to right 1 increment'))

        edit_widen_label = QtWidgets.QLabel(self.transl.tr('Widen'))
        edit_widen_label.setToolTip(self.transl.tr('Widens the active cuts'))
        edit_btn_widenL = QtWidgets.QToolButton(self.main_frame)
        edit_btn_widenL.setArrowType(QtCore.Qt.LeftArrow)
        edit_btn_widenL.clicked.connect(self._on_edit_widenL)
        edit_btn_widenL.setToolTip(self.transl.tr('Widen active cuts 1 increment on left side'))
        edit_btn_widenR = QtWidgets.QToolButton(self.main_frame)
        edit_btn_widenR.setArrowType(QtCore.Qt.RightArrow)
        edit_btn_widenR.clicked.connect(self._on_edit_widenR)
        edit_btn_widenR.setToolTip(self.transl.tr('Widen active cuts 1 increment on right side'))

        edit_trim_label = QtWidgets.QLabel(self.transl.tr('Trim'))
        edit_trim_label.setToolTip(self.transl.tr('Trims the active cuts'))
        edit_btn_trimL = QtWidgets.QToolButton(self.main_frame)
        edit_btn_trimL.setArrowType(QtCore.Qt.LeftArrow)
        edit_btn_trimL.clicked.connect(self._on_edit_trimL)
        edit_btn_trimL.setToolTip(self.transl.tr('Trim active cuts 1 increment on left side'))
        edit_btn_trimR = QtWidgets.QToolButton(self.main_frame)
        edit_btn_trimR.setArrowType(QtCore.Qt.RightArrow)
        edit_btn_trimR.clicked.connect(self._on_edit_trimR)
        edit_btn_trimR.setToolTip(self.transl.tr('Trim active cuts 1 increment on right side'))

        edit_btn_toggle = QtWidgets.QPushButton(self.transl.tr('Toggle'), self.main_frame)
        edit_btn_toggle.clicked.connect(self._on_edit_toggle)
        edit_btn_toggle.setToolTip(self.transl.tr(
            'Toggles the cut at cursor between active and deactive'))
        edit_btn_cursorL = QtWidgets.QToolButton(self.main_frame)
        edit_btn_cursorL.setArrowType(QtCore.Qt.LeftArrow)
        edit_btn_cursorL.clicked.connect(self._on_edit_cursorL)
        edit_btn_cursorL.setToolTip(self.transl.tr('Move cut cursor to left'))
        edit_btn_cursorR = QtWidgets.QToolButton(self.main_frame)
        edit_btn_cursorR.setArrowType(QtCore.Qt.RightArrow)
        edit_btn_cursorR.clicked.connect(self._on_edit_cursorR)
        edit_btn_cursorR.setToolTip(self.transl.tr('Move cut cursor to right'))
        edit_btn_activate_all = QtWidgets.QPushButton(self.transl.tr('All'), self.main_frame)
        edit_btn_activate_all.clicked.connect(self._on_edit_activate_all)
        edit_btn_activate_all.setToolTip(self.transl.tr('Set all cuts to be active'))
        edit_btn_deactivate_all = QtWidgets.QPushButton(self.transl.tr('None'), self.main_frame)
        edit_btn_deactivate_all.clicked.connect(self._on_edit_deactivate_all)
        edit_btn_deactivate_all.setToolTip(self.transl.tr('Set no cuts to be active'))

        # Add the description line edit
        self.le_description = qt_utils.ShadowTextLineEdit(
            self.main_frame, self.transl.tr('Enter description here for template watermark'))
        self.le_description.editingFinished.connect(self._on_description)
        self.le_description.setAlignment(QtCore.Qt.AlignHCenter)

        ######################################################################
        # Layout widgets in the main frame
        ######################################################################

        # vbox contains all of the widgets in the main frame, positioned
        # vertically
        vbox = QtWidgets.QVBoxLayout()

        # Add the figure canvas to the top
        vbox.addWidget(self.fig.canvas)

        # hbox contains all of the control widgets
        # (everything but the canvas)
        hbox = QtWidgets.QHBoxLayout()

        # this grid contains all the lower-left input stuff
        grid = QtWidgets.QGridLayout()

        grid.addWidget(qt_utils.create_hline(), 0, 0, 2, 9, QtCore.Qt.AlignTop)
        grid.addWidget(qt_utils.create_vline(), 0, 0, 9, 1)

        # Add the board width label, board width input line edit,
        # all stacked vertically on the left side.
        grid.addWidget(self.le_board_width_label, 1, 1)
        grid.addWidget(self.le_board_width, 2, 1)
        grid.addWidget(qt_utils.create_vline(), 0, 2, 9, 1)

        # Add the bit width label and its line edit
        grid.addWidget(self.le_bit_width_label, 1, 3)
        grid.addWidget(self.le_bit_width, 2, 3)
        grid.addWidget(qt_utils.create_vline(), 0, 4, 9, 1)

        # Add the bit depth label and its line edit
        grid.addWidget(self.le_bit_depth_label, 1, 5)
        grid.addWidget(self.le_bit_depth, 2, 5)
        grid.addWidget(qt_utils.create_vline(), 0, 6, 9, 1)

        # Add the bit angle label and its line edit
        grid.addWidget(self.le_bit_angle_label, 1, 7)
        grid.addWidget(self.le_bit_angle, 2, 7)
        grid.addWidget(qt_utils.create_vline(), 0, 8, 9, 1)

        grid.addWidget(qt_utils.create_hline(), 3, 0, 2, 9, QtCore.Qt.AlignTop)

        grid.setRowStretch(2, 10)

        # Add the wood combo boxes
        grid.addWidget(self.cb_wood_label[0], 4, 1)
        grid.addWidget(self.cb_wood_label[1], 4, 3)
        grid.addWidget(self.cb_wood_label[2], 4, 5)
        grid.addWidget(self.cb_wood_label[3], 4, 7)
        grid.addWidget(self.cb_wood[0], 5, 1)
        grid.addWidget(self.cb_wood[1], 5, 3)
        grid.addWidget(self.cb_wood[2], 5, 5)
        grid.addWidget(self.cb_wood[3], 5, 7)

        # Add double* thickness line edits
        grid.addWidget(self.le_boardm_label[0], 6, 5)
        grid.addWidget(self.le_boardm_label[1], 6, 7)
        grid.addWidget(self.le_boardm[0], 7, 5)
        grid.addWidget(self.le_boardm[1], 7, 7)

        grid.addWidget(qt_utils.create_hline(), 8, 0, 2, 9, QtCore.Qt.AlignTop)

        hbox.addLayout(grid)

        # Create the layout of the Equal spacing controls
        hbox_es = QtWidgets.QHBoxLayout()

        vbox_es_slider0 = QtWidgets.QVBoxLayout()
        vbox_es_slider0.addWidget(self.es_slider0_label)
        vbox_es_slider0.addWidget(self.es_slider0)
        hbox_es.addLayout(vbox_es_slider0)

        vbox_es_slider1 = QtWidgets.QVBoxLayout()
        vbox_es_slider1.addWidget(self.es_slider1_label)
        vbox_es_slider1.addWidget(self.es_slider1)
        hbox_es.addLayout(vbox_es_slider1)

        hbox_es.addWidget(self.cb_es_centered)

        # Create the layout of the Variable spacing controls.  Given only one
        # item, this is overkill, but the coding allows us to add additional
        # controls later.
        # hbox_vs = QtWidgets.QVBoxLayout()
        hbox_vs = QtWidgets.QHBoxLayout()

        vbox_vs_cb = QtWidgets.QVBoxLayout()
        vbox_vs_cb.addWidget(self.cb_vsfingers_label)
        vbox_vs_cb.addWidget(self.cb_vsfingers)
        hbox_vs.addLayout(vbox_vs_cb)

        vbox_vs_slider0 = QtWidgets.QVBoxLayout()
        vbox_vs_slider0.addWidget(self.vs_slider0_label)
        vbox_vs_slider0.addWidget(self.vs_slider0)
        hbox_vs.addLayout(vbox_vs_slider0)

        hbox_vs.addWidget(self.cb_vs_inverted)

        # Create the layout of the edit spacing controls
        hbox_edit = QtWidgets.QHBoxLayout()
        grid_edit = QtWidgets.QGridLayout()
        grid_edit.addWidget(qt_utils.create_hline(), 0, 0, 2, 16, QtCore.Qt.AlignTop)
        grid_edit.addWidget(qt_utils.create_hline(), 2, 0, 2, 16, QtCore.Qt.AlignTop)
        grid_edit.addWidget(qt_utils.create_vline(), 0, 0, 6, 1)
        label_active_cut_select = QtWidgets.QLabel(self.transl.tr('Active Cut Select'))
        label_active_cut_select.setToolTip(self.transl.tr('Tools that select the active cuts'))
        grid_edit.addWidget(label_active_cut_select, 1, 1, 1, 3, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_btn_toggle, 3, 1, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_btn_cursorL, 4, 1, QtCore.Qt.AlignRight)
        grid_edit.addWidget(edit_btn_cursorR, 4, 2, QtCore.Qt.AlignLeft)
        grid_edit.addWidget(edit_btn_activate_all, 3, 3)
        grid_edit.addWidget(edit_btn_deactivate_all, 4, 3)
        grid_edit.addWidget(qt_utils.create_vline(), 0, 4, 6, 1)
        label_active_cut_ops = QtWidgets.QLabel(self.transl.tr('Active Cut Operators'))
        label_active_cut_ops.setToolTip(self.transl.tr('Edit operations applied to active cuts'))
        grid_edit.addWidget(label_active_cut_ops, 1, 5, 1, 10, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_move_label, 3, 5, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_btn_moveL, 4, 5, QtCore.Qt.AlignRight)
        grid_edit.addWidget(edit_btn_moveR, 4, 6, QtCore.Qt.AlignLeft)
        grid_edit.addWidget(qt_utils.create_vline(), 2, 7, 4, 1)
        grid_edit.addWidget(edit_widen_label, 3, 8, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_btn_widenL, 4, 8, QtCore.Qt.AlignRight)
        grid_edit.addWidget(edit_btn_widenR, 4, 9, QtCore.Qt.AlignLeft)
        grid_edit.addWidget(qt_utils.create_vline(), 2, 10, 4, 1)
        grid_edit.addWidget(edit_trim_label, 3, 11, 1, 2, QtCore.Qt.AlignHCenter)
        grid_edit.addWidget(edit_btn_trimL, 4, 11, QtCore.Qt.AlignRight)
        grid_edit.addWidget(edit_btn_trimR, 4, 12, QtCore.Qt.AlignLeft)
        grid_edit.addWidget(qt_utils.create_vline(), 2, 13, 4, 1)
        grid_edit.addWidget(edit_btn_add, 3, 14)
        grid_edit.addWidget(edit_btn_del, 4, 14)
        grid_edit.addWidget(qt_utils.create_vline(), 0, 15, 6, 1)
        grid_edit.addWidget(qt_utils.create_hline(), 5, 0, 2, 16, QtCore.Qt.AlignTop)
        grid_edit.setSpacing(5)

        hbox_edit.addLayout(grid_edit)
        hbox_edit.addStretch(1)
        hbox_edit.addWidget(edit_btn_undo)

        # Add the spacing layouts as Tabs
        self.tabs_spacing = QtWidgets.QTabWidget()
        tab_es = QtWidgets.QWidget()
        tab_es.setLayout(hbox_es)

        self.tabs_spacing.addTab(tab_es, self.transl.tr('Equal'))
        tab_vs = QtWidgets.QWidget()
        tab_vs.setLayout(hbox_vs)

        self.tabs_spacing.addTab(tab_vs, self.transl.tr('Variable'))
        tab_edit = QtWidgets.QWidget()
        tab_edit.setLayout(hbox_edit)

        self.tabs_spacing.addTab(tab_edit, self.transl.tr('Editor'))
        self.tabs_spacing.currentChanged.connect(self._on_tabs_spacing)
        tip = self.transl.tr('These tabs specify the layout algorithm for the cuts.')
        self.tabs_spacing.setToolTip(tip)

        # The tab indices should be set in the order they're defined, but this ensures it
        self.equal_spacing_id = self.tabs_spacing.indexOf(tab_es)
        self.var_spacing_id = self.tabs_spacing.indexOf(tab_vs)
        self.edit_spacing_id = self.tabs_spacing.indexOf(tab_edit)
        # set default spacing tab to Equal
        self.spacing_index = self.equal_spacing_id
        self.tabs_spacing.setCurrentIndex(self.spacing_index)

        # either add the spacing Tabs to the right of the line edits
        vbox_tabs = QtWidgets.QVBoxLayout()
        vbox_tabs.addWidget(self.tabs_spacing)
        vbox_tabs.addWidget(self.le_description)
        vbox_tabs.addStretch(1)
        hbox.addStretch(1)
        hbox.addLayout(vbox_tabs)
        vbox.addLayout(hbox)

        # Lay it all out
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

        # Finalize some settings
        self.cb_vsfingers.activated.connect(self._on_cb_vsfingers)
        self.cb_vsfingers.highlighted.connect(self._on_cb_vsfingers)
        self.cb_wood[0].activated.connect(self._on_wood0)
        self.cb_wood[1].activated.connect(self._on_wood1)
        self.cb_wood[2].activated.connect(self._on_wood2)
        self.cb_wood[3].activated.connect(self._on_wood3)
        self.cb_wood[0].highlighted.connect(self._on_wood0)
        self.cb_wood[1].highlighted.connect(self._on_wood1)
        self.cb_wood[2].highlighted.connect(self._on_wood2)
        self.cb_wood[3].highlighted.connect(self._on_wood3)
        self._on_wood(0)
        self._on_wood(1)
        self._on_wood(2)
        self._on_wood(3)
        self.update_tooltips()

    def update_cb_vsfingers(self, vMin, vMax, value):
        '''
        Updates the combobox for Variable spacing Fingers.
        '''
        self.cb_vsfingers.clear()
        for i in range(vMin, vMax + 1, 1):
            self.cb_vsfingers.addItem(str(i))
        i = self.cb_vsfingers.findText(str(value))
        self.cb_vsfingers.setCurrentIndex(i)

    def update_tooltips(self):
        '''
        [Re]sets the tool tips for widgets whose tips depend on user settings
        '''

        disable = ''
        if self.spacing_index == self.edit_spacing_id:
            disable = self.transl.tr('  <b>Cannot change if in Editor mode.</b>')

        disable_double = disable
        if not self.boards[2].active:
            disable_double = self.transl.tr(
                '  <b>Cannot change unless "Double Board" is not NONE.</b>')
        disable_dd = disable
        if not self.boards[3].active:
            disable_dd = self.transl.tr(
                '  <b>Cannot change unless "Double-Double Board" is not NONE.</b>')

        self.le_board_width_label.setToolTip(self.doc.board_width() + disable)
        self.le_board_width.setToolTip(self.doc.board_width() + disable)
        self.le_bit_width_label.setToolTip(self.doc.bit_width() + disable)
        self.le_bit_width.setToolTip(self.doc.bit_width() + disable)
        self.le_bit_depth_label.setToolTip(self.doc.bit_depth() + disable)
        self.le_bit_depth.setToolTip(self.doc.bit_depth() + disable)
        self.le_bit_angle_label.setToolTip(self.doc.bit_angle() + disable)
        self.le_bit_angle.setToolTip(self.doc.bit_angle() + disable)

        self.cb_wood_label[0].setToolTip(self.doc.top_board() + disable)
        self.cb_wood[0].setToolTip(self.doc.top_board() + disable)
        self.cb_wood_label[1].setToolTip(self.doc.bottom_board() + disable)
        self.cb_wood[1].setToolTip(self.doc.bottom_board() + disable)
        self.cb_wood_label[2].setToolTip(self.doc.double_board() + disable)
        self.cb_wood[2].setToolTip(self.doc.double_board() + disable)
        self.cb_wood_label[3].setToolTip(self.doc.dd_board() + disable_double)
        self.cb_wood[3].setToolTip(self.doc.dd_board() + disable_double)

        self.le_boardm_label[0].setToolTip(self.doc.double_thickness() + disable_double)
        self.le_boardm[0].setToolTip(self.doc.double_thickness() + disable_double)
        self.le_boardm_label[1].setToolTip(self.doc.dd_thickness() + disable_dd)
        self.le_boardm[1].setToolTip(self.doc.dd_thickness() + disable_dd)

        self.es_slider0_label.setToolTip(self.doc.es_slider0())
        self.es_slider0.setToolTip(self.doc.es_slider0())
        self.es_slider1_label.setToolTip(self.doc.es_slider1())
        self.es_slider1.setToolTip(self.doc.es_slider1())
        self.cb_es_centered.setToolTip(self.doc.es_centered())
        self.cb_vsfingers_label.setToolTip(self.doc.cb_vsfingers())
        self.cb_vsfingers.setToolTip(self.doc.cb_vsfingers())

    def create_status_bar(self):
        '''
        Creates a status message bar that is placed at the bottom of the
        main frame.
        '''
        tt_message = self.transl.tr('Status of the last operation.')
        tt_fit = self.transl.tr('Maximum overlap and gap for the current joint.'\
                 ' Too much overlap will cause an interference fit,'\
                 ' while too much gap will result in a loose-fitting joint.')

        # Create the fonts and labels for each field
        font = QtGui.QFont('Times', 14)
        fm = QtGui.QFontMetrics(font)
        fontL = QtGui.QFont(font)
        fontL.setBold(True)
        fmL = QtGui.QFontMetrics(fontL)

        fit_text = self.transl.tr('Fit:')
        fit = QtWidgets.QLabel(fit_text)
        fit.setFont(fontL)
        fit.setFixedWidth(fmL.width(fit_text))
        fit.setToolTip(tt_fit)

        status_text = self.transl.tr('Status:')
        status = QtWidgets.QLabel(status_text)
        status.setFont(fontL)
        status.setFixedWidth(fmL.width(status_text))
        status.setToolTip(tt_message)

        # Create the label widgets that will change their text
        style = QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised
        self.status_message_label = QtWidgets.QLabel(self.transl.tr('MESSAGE'))
        self.status_message_label.setFont(font)
        self.status_message_label.setFrameStyle(style)
        self.status_message_label.setToolTip(tt_message)

        self.status_fit_label = QtWidgets.QLabel(self.transl.tr('FIT'))
        w = fm.width(self.transl.tr('Max gap = 0.0000 mm  Max overlap = 0.0000 mm'))
        self.status_fit_label.setFixedWidth(w)
        self.status_fit_label.setFont(font)
        self.status_fit_label.setFrameStyle(style)
        self.status_fit_label.setToolTip(tt_fit)

        # Add labels to statusbar
        self.statusbar = self.statusBar()
        #self.status_message_label.setAlignment(QtCore.Qt.AlignRight)
        self.statusbar.addPermanentWidget(fit, 1)
        self.statusbar.addPermanentWidget(self.status_fit_label, 2)
        self.statusbar.addPermanentWidget(status, 1)
        self.statusbar.addPermanentWidget(self.status_message_label, 2)

        self.status_message(self.transl.tr('Ready'))

    def status_message(self, msg, warning=False, flash_len_ms=None):
        '''
        Displays a message to the status bar
        '''
        if warning:
            style = 'background-color: red; color: white'
            self.status_message_label.setStyleSheet(style)
        else:
            self.status_message_label.setStyleSheet('color: green')
        self.status_message_label.setText(msg)
        if flash_len_ms is not None:
            QtCore.QTimer.singleShot(flash_len_ms, self._on_flash_status_off)

    def status_fit(self):
        '''
        Updates the fit parameters in the status bar.
        '''
        if self.fig.geom is None:
            return
        msg = self.transl.tr('Max gap = %.3f%s  Max overlap = %.3f%s')
        gap = self.fig.geom.max_gap
        overlap = self.fig.geom.max_overlap
        warn_gap = self.units.abstract_to_increments(self.config.warn_gap, False)
        warn_overlap = self.units.abstract_to_increments(self.config.warn_overlap, False)
        u = self.units.units_string()
        if overlap > warn_overlap or gap > warn_gap:
            style = 'background-color: red; color: white'
            self.status_fit_label.setStyleSheet(style)
        else:
            self.status_fit_label.setStyleSheet('color: green')
        gap = self.units.increments_to_length(gap)
        overlap = self.units.increments_to_length(overlap)
        self.status_fit_label.setText(msg % (gap, u, overlap, u))

    def draw(self):
        '''(Re)draws the template and boards'''
        if self.config.debug:
            print('draw')
        self.template = router.Incra_Template(self.units, self.boards)
        self.fig.draw(self.template, self.boards, self.bit, self.spacing, self.woods,
                      self.description)
        self.status_fit()

    def reinit_spacing(self):
        '''
        Re-initializes the joint spacing objects.  This must be called
        when the router bit or board change dimensions.
        '''
        spacing_index = self.tabs_spacing.currentIndex()

        # Re-create the spacings objects
        if spacing_index == self.equal_spacing_id:
            self.equal_spacing = spacing.Equally_Spaced(self.bit, self.boards, self.config)
        elif spacing_index == self.var_spacing_id:
            self.var_spacing = spacing.Variable_Spaced(self.bit, self.boards, self.config)
        elif spacing_index == self.edit_spacing_id:
            self.edit_spacing = spacing.Edit_Spaced(self.bit, self.boards, self.config)
        else:
            raise ValueError(self.transl.tr('Bad value for spacing_index %d') % self.spacing_index)

        # Switch spacing index if now calculation issues
        self.spacing_index = self.tabs_spacing.currentIndex()
        self.set_spacing_widgets()

    def set_spacing_widgets(self):
        '''
        Sets the spacing widget parameters
        '''
        # enable/disable changing parameters, depending upon spacing algorithm
        les = [self.le_board_width, self.le_board_width_label,
               self.le_bit_width, self.le_bit_width_label,
               self.le_bit_depth, self.le_bit_depth_label,
               self.le_bit_angle, self.le_bit_angle_label]
        les.extend(self.cb_wood)
        les.extend(self.cb_wood_label)
        les.extend(self.le_boardm)
        les.extend(self.le_boardm_label)
        if self.spacing_index == self.edit_spacing_id:
            for le in les:
                le.blockSignals(True)
                le.setEnabled(False)
                le.setStyleSheet("color: gray;")
                le.blockSignals(False)
        else:
            for le in les:
                le.blockSignals(True)
                le.setEnabled(True)
                le.setStyleSheet("color: black;")
                le.blockSignals(False)
            if not self.boards[2].active:
                disable = self.le_boardm
                disable.extend(self.le_boardm_label)
                disable.append(self.cb_wood[3])
                disable.append(self.cb_wood_label[3])
                for le in disable:
                    le.blockSignals(True)
                    le.setEnabled(False)
                    le.setStyleSheet("color: gray;")
                    le.blockSignals(False)
            if not self.boards[3].active:
                disable = [self.le_boardm[1], self.le_boardm_label[1]]
                for le in disable:
                    le.blockSignals(True)
                    le.setEnabled(False)
                    le.setStyleSheet("color: gray;")
                    le.blockSignals(False)

        # Set up the various widgets for each spacing option
        if self.spacing_index == self.equal_spacing_id:
            # Equal spacing widgets
            params = self.equal_spacing.params
            p = params['Spacing']
            self.es_slider0.blockSignals(True)
            self.es_slider0.setMinimum(p.vMin)
            self.es_slider0.setMaximum(p.vMax)
            self.es_slider0.setValue(p.v)
            utils.set_slider_tick_interval(self.es_slider0)
            self.es_slider0.blockSignals(False)
            p = params['Width']
            self.es_slider1.blockSignals(True)
            self.es_slider1.setMinimum(p.vMin)
            self.es_slider1.setMaximum(p.vMax)
            self.es_slider1.setValue(p.v)
            utils.set_slider_tick_interval(self.es_slider1)
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
            self.cb_vsfingers.blockSignals(True)
            self.update_cb_vsfingers(p.vMin, p.vMax, p.v)
            self.cb_vsfingers.blockSignals(False)
            self.var_spacing.set_cuts()
            self.cb_vsfingers_label.setText(self.transl.tr("Fingers")) #self.transl.tr(self.var_spacing.labels[0])
            self.spacing = self.var_spacing
        elif self.spacing_index == self.edit_spacing_id:
            # Edit spacing parameters.  Currently, this has no parameters, and
            # uses as a starting spacing whatever the previous spacing set.
            self.edit_spacing.set_cuts(self.spacing.cuts)
            self.spacing = self.edit_spacing
        else:
            raise ValueError(self.transl.tr('Bad value for spacing_index %d') % self.spacing_index)

        self.update_tooltips()

    def update_config_path(self, filename):
        '''
        Update config file with the last saved or opened file name
        passed in params.
        '''
        self.config.last_path = str(filename)
        (working_dir, fname) = os.path.split(os.path.splitext(self.config.last_path)[0])
        prefix = fname.rstrip('0123456789')

        if working_dir != self.working_dir or prefix != self.prefix:
            self.working_dir = working_dir
            self.prefix = prefix
            # Save the last path and file name
            c = config_file.Configuration()
            c.write_config(self.config.__dict__.copy())
            self.file_saved = True

        self.setWindowTitle(filename + ' \u2014 pyRouterJig')

    @QtCore.pyqtSlot(int)
    def _on_tabs_spacing(self, index):
        '''Handles changes to spacing algorithm'''
        if self.config.debug:
            print('_on_tabs_spacing')
        if self.spacing_index == self.edit_spacing_id and index != self.edit_spacing_id and \
            self.spacing.changes_made():
            msg = self.transl.tr('You are exiting the Editor, which will discard'\
                  ' any changes made in the Editor.'\
                  '\n\nAre you sure you want to do this?')
            reply = QtWidgets.QMessageBox.question(self, self.transl.tr('Message'), msg,
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                self.tabs_spacing.setCurrentIndex(self.spacing_index)
                return
        try:
            self.reinit_spacing()
        except:
            # Rollback tab switch in case of exception
            if index == self.var_spacing_id:
                self.tabs_spacing.setCurrentIndex(self.spacing_index)
            raise

        self.draw()
        self.status_message(self.transl.tr('Changed to spacing algorithm %s')\
                            % str(self.tabs_spacing.tabText(index)))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_width(self):
        '''Handles changes to bit width'''
        if self.config.debug:
            print('_on_bit_width')
        val = qt_utils.set_router_value(self.le_bit_width, self.bit, 'width',
                                        'set_width_from_string')
        if val is not None:
            self.reinit_spacing()
            self.draw()
            self.status_message(self.transl.tr('Changed bit width to ') + val)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_depth(self):
        '''Handles changes to bit depth'''
        if self.config.debug:
            print('_on_bit_depth')
        val = qt_utils.set_router_value(self.le_bit_depth, self.bit, 'depth',
                                        'set_depth_from_string')
        if val is not None:
            for b in self.boards:
                b.set_height(self.bit)
            self.reinit_spacing()
            self.draw()
            self.status_message(self.transl.tr('Changed bit depth to ') + val)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_bit_angle(self):
        '''Handles changes to bit angle'''
        if self.config.debug:
            print('_on_bit_angle')
        val = qt_utils.set_router_value(self.le_bit_angle, self.bit, 'angle',
                                        'set_angle_from_string', True)
        if val is not None:
            self.reinit_spacing()
            self.draw()
            self.status_message(self.transl.tr('Changed bit angle to ') + val)
            self.file_saved = False
            self.threeDS_enabler()

    @QtCore.pyqtSlot()
    def _on_board_width(self):
        '''Handles changes to board width'''
        if self.config.debug:
            print('_on_board_width')
        val = qt_utils.set_router_value(self.le_board_width, self.boards[0], 'width',
                                        'set_width_from_string')
        if val is not None:
            # Check if board with is applicable for a tab
            err = False
            msg = ''
            if self.spacing_index == self.var_spacing_id and \
                    not spacing.Variable_Spaced.is_board_width_ok(self.bit, self.boards):
                err = True
                msg = self.transl.tr(spacing.Variable_Spaced.msg)
            if self.spacing_index == self.equal_spacing_id and \
                    not spacing.Equally_Spaced.is_board_width_ok(self.bit, self.boards,
                                                                 self.config):
                err = True
                msg = self.transl.tr(spacing.Equally_Spaced.msg)
            if err:
                self.boards[0].width = self.boards[1].width
                self.le_board_width.setText(self.units.increments_to_string(self.boards[0].width))
                self.status_message(self.transl.tr('Board width is not changed'))
                raise spacing.Spacing_Exception(msg)

            for b in self.boards[1:]:
                b.width = self.boards[0].width

            self.reinit_spacing()
            self.draw()
            self.status_message(self.transl.tr('Changed board width to ') + val)
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_description(self):
        '''Handles changes to description'''
        if self.config.debug:
            print('_on_description')
        if self.le_description.isModified():
            self.description = str(self.le_description.text())
            self.draw()
            self.status_message(self.transl.tr(
                'Changed description to "{}"').format(self.description))
            self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_es_slider0(self, value):
        '''Handles changes to the equally-spaced slider spacing'''
        if self.config.debug:
            print('_on_es_slider0', value)
        self.equal_spacing.params['Spacing'].v = value
        self.equal_spacing.set_cuts()
        self.es_slider0_label.setText(self.equal_spacing.labels[0])
        self.draw()
        self.status_message(self.transl.tr('Changed slider %s') % str(self.es_slider0_label.text()))
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
        self.status_message(self.transl.tr('Changed slider %s') % str(self.es_slider1_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_vs_slider0(self, value):
        '''Handles changes to the variable spaced slider D'''
        if self.config.debug:
            print('_on_vs_slider0', value)
        self.var_spacing.params['Spacing'].v = value
        self.var_spacing.set_cuts()
        self.vs_slider0_label.setText(self.var_spacing.labels[1])
        self.draw()
        self.status_message(self.transl.tr('Changed slider %s') % str(self.vs_slider0_label.text()))
        self.file_saved = False

    @QtCore.pyqtSlot()
    def _cb_vs_inverted(self):
        '''Handles changes inverse variable fingers'''
        if self.config.debug:
            print('_cb_vs_inverted')
        self.var_spacing.params['Inverted'].v = self.cb_vs_inverted.isChecked()
        self.var_spacing.calc_var_params()

        # ...combox box for fingers
        p = self.var_spacing.params['Spacing']
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.v)

        self.var_spacing.set_cuts()
        self.draw()
        if self.var_spacing.params['Inverted'].v:
            self.status_message(self.transl.tr('Checked Inverted.'))
        else:
            self.status_message(self.transl.tr('Unchecked Inverted.'))
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
            self.status_message(self.transl.tr('Checked Centered.'))
        else:
            self.status_message(self.transl.tr('Unchecked Centered.'))
        self.file_saved = False

    @QtCore.pyqtSlot(int)
    def _on_cb_vsfingers(self, index):
        '''Handles changes to the variable-spaced slider Fingers'''
        if self.config.debug:
            print('_on_cb_vsfingers', index)
        self.var_spacing.params['Fingers'].v = int(self.cb_vsfingers.itemText(index))
        self.var_spacing.calc_var_params()

        # ...combox box for fingers
        p = self.var_spacing.params['Spacing']
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.v)
        self.var_spacing.set_cuts()

        self.cb_vsfingers_label.setText(self.var_spacing.labels[0])
        self.draw()
        self.status_message(self.transl.tr('%s ') % str(self.cb_vsfingers_label.text()) + \
                            self.cb_vsfingers.itemText(index))
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

        # Form the default filename prefix
        prefix = self.prefix # was 'pyrouterjig'
        suffix = 'png'
        if self.screenshot_index is None:
            self.screenshot_index = utils.get_file_index(self.working_dir, prefix, suffix)
        fname = prefix
        fname += str(self.screenshot_index)

        # Get the file name.  The default name is indexed on the number of
        # times this function is called.  If a screenshot, don't prompt for
        # the filename and use the default name
        defname = os.path.join(self.working_dir, fname)
        if do_screenshot:
            filename = defname + '.' + suffix
        else:
            # This is the simple approach to set the filename, but doesn't allow
            # us to update the working_dir, if the user changes it.
            # filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', \
            #                     defname, 'Portable Network Graphics (*.png)')
            # ... so here is now we do it:
            dialog = QtWidgets.QFileDialog(self, self.transl.tr('Save file'), defname,
                                           'Portable Network Graphics (*.png)')

            dialog.setDefaultSuffix(suffix)
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            filename = None
            if dialog.exec_():
                filenames = dialog.selectedFiles()

                # Save updated config if path or base name changed
                self.update_config_path(filenames[0])
                filename = self.config.last_path.strip()

            if filename is None:
                self.status_message(self.transl.tr('File not saved'), warning=True)
                return

        dpiX = 300
        dpiY = 300
        # Save the file with metadata
        if do_screenshot:
            p_screen = QtWidgets.QApplication.primaryScreen()
            dpiX = p_screen.logicalDotsPerInchX()
            dpiY = p_screen.logicalDotsPerInchY()
            image = p_screen.grabWindow(self.winId())
        else:
            image = self.fig.image(self.template, self.boards, self.bit, self.spacing,
                                   self.woods, self.description)
            dpiY = self.fig.dpi
            dpiX = self.fig.dpi

        s = serialize.serialize(self.bit, self.boards, self.spacing,
                                self.config, self.description)

        # we use UUEC encoding so need more attributes in the image file
        # QT5 does not work propertly with PNG text; use PIL as workaround

        # Save QT image into stream and get it back into PIL to avoid native
        # pil conversion risks
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QIODevice.ReadWrite)
        image.save(buffer, "PNG")
        pio = BytesIO()
        pio.write(buffer.data())
        pio.seek(0)
        buffer.close()
        pilimg = Image.open(pio)

        # convert image to unifyed profile
        # however we know that the image taken from monitor so need to convert monitor to sRGB
        # feel free to use other profile if any
        if platform.system() != 'Darwin':
            monitor_profile = ImageCms.get_display_profile()
            if monitor_profile != None:
                monitor_profile = ImageCms.createProfile('sRGB') # rare happen case - non profiled monitor!!!!

            srgb = ImageCms.createProfile('sRGB')

            # here we convert image to the profile. and got the profile into info
            # The point is that the info will lost on save so we have to assign the proper one profile when safe the image
            pilimg = ImageCms.profileToProfile(pilimg, monitor_profile, srgb)

        # uncomment the line below to set color profiling off
        info = PngImagePlugin.PngInfo()

        info.add_text('pyRouterJig', s)
        info.add_text('pyRouterJig_v', utils.VERSION)

        r = True
        try:
            pilimg.save(filename, 'png', pnginfo=info, dpi=(dpiX, dpiY) )
        except OSError:
            r = False

        if r:
            self.status_message(self.transl.tr('Saved to file %s') % filename)
            if self.screenshot_index is not None:
                self.screenshot_index += 1
        else:
            self.status_message(self.transl.tr('Unable to save to file %s') % filename,
                                warning=True)

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
            msg = self.transl.tr('Current joint not saved.'\
                  ' Opening a new file will overwrite the current joint.'\
                  '\n\nAre you sure you want to do this?')
            reply = QtWidgets.QMessageBox.question(self, self.transl.tr('Message'), msg,
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                return

        # Get the file name
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.transl.tr('Open file'),
            self.working_dir,
            'Portable Network Graphics (*.png)')
        # filename = str(filename).strip()
        if not filename:
            self.status_message(self.transl.tr('File open aborted'), warning=True)
            return

        # From the image file, parse the metadata.
        image = Image.open(filename)
        s = image.info['pyRouterJig']

        if not s:
            msg = self.transl.tr('File %s does not contain pyRouterJig data.  The PNG file'\
                  ' must have been saved using pyRouterJig.') % filename
            QtWidgets.QMessageBox.warning(self, self.transl.tr('Error'), msg)
            return

        # backwards compatibility
        (bit, boards, sp, sp_type, description) = \
            serialize.unserialize(s, self.config, ('pyRouterJig_v' in image.info.keys()),
                                  self.transl)

        if self.bit.units.metric != bit.units.metric:
            scales_name = 'English'
            if bit.units.metric:
                scales_name = 'Metric'
            msg = self.transl.tr('Unable to use the file {}.'
                                 '\nJoin designed for another scale system.\n'
                                 'Switch pyRouterJig into {} system first').\
                                format(filename, scales_name)
            QtWidgets.QMessageBox.warning(self, self.transl.tr('Error'), msg)
            return

        # Reset the dependent data
        self.bit = bit
        self.boards = boards
        self.units = self.bit.units
        self.doc = doc.Doc(self.units)
        self.template = router.Incra_Template(self.units, self.boards)
        self.description = description

        # ... set the wood selection for each board.  If the wood does not
        # exist, set to a wood we know exists.  This can happen if the wood
        # image files don't exist across users.
        # self.boards[i].wood is newstr type use str(self.boards[i].wood) is for
        # old files compatibility
        for i in range(4):
            if self.boards[i].wood is None:
                self.boards[i].set_wood('NONE')
            elif str(self.boards[i].wood) not in self.woods.keys():
                local_wood = self.transl.tr(str(self.boards[i].wood))
                if local_wood in self.woods.keys():
                    self.boards[i].set_wood(local_wood)
                else :
                    self.boards[i].set_wood(self.transl.tr('DiagCrossPattern'))

            # backwards compatibility fix
            self.boards[i].wood = str(self.boards[i].wood)
            j = self.cb_wood[i].findText(self.boards[i].wood)
            self.cb_wood[i].setCurrentIndex(j)

        # ... set double* board input parameters.  The double* inputs are
        # activated/deactivated in set_spacing_parameters(), called below
        if self.boards[2].active:
            self.le_boardm[0].setText(self.units.increments_to_string(self.boards[2].dheight))
            if self.boards[3].active:
                self.le_boardm[1].setText(self.units.increments_to_string(self.boards[3].dheight))
        else:
            i = self.cb_wood[3].findText('NONE')
            self.cb_wood[3].setCurrentIndex(i)

        # ... set spacing cuts and tabs
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

        # ... set line edit parameters
        self.le_board_width.setText(self.units.increments_to_string(self.boards[0].width))
        self.le_bit_width.setText(self.units.increments_to_string(self.bit.width))
        self.le_bit_depth.setText(self.units.increments_to_string(self.bit.depth))
        self.le_bit_angle.setText(str(self.bit.angle))
        self.le_description.setText(self.description)
        self.set_spacing_widgets()

        self.draw()

        # Mark "no changes", save path, and set window title
        self.update_config_path(filename)

    def threeDS_enabler(self):
        '''
        Enables / Disables 3DS file save, depending on joint and bit
        properties
        '''
        if self.config.debug:
            print('threeDS_enabler')

        if self.bit.angle > 0 or self.boards[2].active:
            self.threeDS_action.setEnabled(False)
        else:
            self.threeDS_action.setEnabled(True)

    @QtCore.pyqtSlot()
    def _on_3ds(self):
        '''
        Handles export to 3DS file events.
        '''
        if self.config.debug:
            print('_on_3ds')

        fname = 'pyrouterjig.3ds'

        # Get the file name
        defname = os.path.join(self.working_dir, fname)
        dialog = QtWidgets.QFileDialog(self, self.transl.tr('Export joint'), defname,
                                       'Autodesk 3DS file (*.3ds)')
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        filename = None
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            d = str(dialog.directory().path())
            # force recomputation of index, next time around, if path changed
            if d != self.working_dir:
                self.screenshot_index = None
            self.working_dir = d
            filename = str(filenames[0]).strip()
        if filename is None:
            self.status_message(self.transl.tr('Joint not exported'), warning=True)
            return

        threeDS.joint_to_3ds(filename, self.boards, self.bit, self.spacing)
        self.status_message(self.transl.tr('Exported to file %s') % filename)

    @QtCore.pyqtSlot()
    def _on_print(self):
        '''Handles print events'''
        if self.config.debug:
            print('_on_print')

        r = self.fig.print(self.template, self.boards, self.bit, self.spacing,
                           self.woods, self.description)
        if r:
            self.status_message(self.transl.tr('Figure printed'))
        else:
            self.status_message(self.transl.tr('Figure not printed'), warning=True)

    @QtCore.pyqtSlot()
    def _on_print_table(self):
        '''Handles printing the router pass location table'''
        if self.config.debug:
            print('_on_print_table')

        prefix = 'table_'
        suffix = '.txt'
        if self.table_index is None:
            self.table_index = utils.get_file_index(self.working_dir, prefix, suffix)

        fname = prefix + str(self.table_index) + suffix
        filename = os.path.join(self.working_dir, fname)
        title = router.create_title(self.boards, self.bit, self.spacing)
        utils.print_table(filename, self.boards, title)
        self.table_index += 1
        self.status_message(self.transl.tr('Saved router pass location table to %s') % filename)

    @QtCore.pyqtSlot()
    def _on_about(self):
        '''Handles about dialog event'''
        if self.config.debug:
            print('_on_about')

        box = QtWidgets.QMessageBox(self)
        s = self.transl.tr('<font size=5 color=red>Welcome to <i>pyRouterJig</i> !</font>')
        s += self.transl.tr('<h3>Version: %s</h3>') % utils.VERSION
        box.setText(s + self.doc.short_desc() + self.doc.license())
        box.setTextFormat(QtCore.Qt.RichText)
        box.show()

    @QtCore.pyqtSlot()
    def _on_preferences(self):
        '''Handles opening and changing preferences'''
        if self.config.debug:
            print('_on_preferences')

        self.config_window.initialize()
        r = self.config_window.exec_()
        if r == 0:
            self.status_message(self.transl.tr('No changes made to configuration file.'),
                                warning=True)
        else:
            self.status_message(self.transl.tr('Preference changes saved in configuration file.'))
            self.bit.bit_gentle = self.config_window.bit.bit_gentle

        # Update widgets that may have changed
        actions = [self.finger_size_action,
                   self.caul_action,
                   self.pass_id_action,
                   self.pass_location_action]
        for a in actions:
            a.blockSignals(True)
        self.finger_size_action.setChecked(self.config.show_finger_widths)
        self.caul_action.setChecked(self.config.show_caul)
        self.fit_action.setChecked(self.config.show_fit)
        self.pass_id_action.setChecked(self.config.show_router_pass_identifiers)
        self.pass_location_action.setChecked(self.config.show_router_pass_locations)
        for a in actions:
            a.blockSignals(False)

        (woods, patterns) = qt_utils.create_wood_dict(self.config.wood_images, self.transl)
        self.woods = copy.deepcopy(woods)
        self.woods.update(patterns)
        for i in range(len(self.boards)):
            cb = self.cb_wood[i]
            has_none = (cb.findText('NONE') >= 0)
            selected_wood = cb.currentText()
            current_wood = cb.currentData()
            if selected_wood != 'NONE':
                current_wood = self.config.default_wood
            self.populate_wood_combo_box(cb, woods, patterns, current_wood, has_none)
            if selected_wood != 'NONE':
                self.boards[i].set_wood(cb.currentText())
        self.draw()

    @QtCore.pyqtSlot()
    def _on_exit(self):
        '''Handles code exit events'''
        if self.config.debug:
            print('_on_exit')
        if self.file_saved:
            # QtGui.qApp.quit()
            QtWidgets.qApp.quit()
        else:
            msg = self.transl.tr('Figure was changed but not saved.'
                                 ' Are you sure you want to quit?')
            reply = QtWidgets.QMessageBox.question(self, 'Message', msg,
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                QtWidgets.qApp.quit()

    @QtCore.pyqtSlot()
    def _on_doclink(self):
        '''Handles doclink event'''
        if self.config.debug:
            print('_on_doclink')

        # webbrowser.open('http://lowrie.github.io/pyRouterJig/documentation.html')
        webbrowser.open('http://lowrie.github.io/pyRouterJig/overview/')

    def _on_wood(self, iwood, index=None, reinit=False):
        '''Handles all changes in wood'''
        if self.config.debug:
            print('_on_wood', iwood, index)
        if index is None:
            index = max(0, self.cb_wood[iwood].currentIndex())
            self.cb_wood[iwood].setCurrentIndex(index)
        s = str(self.cb_wood[iwood].itemText(index))
        label = str(self.cb_wood_label[iwood].text())
        if s != 'NONE':
            self.boards[iwood].set_wood(s)
        if reinit:
            self.reinit_spacing()
        self.draw()
        msg = self.transl.tr('Changed %s to %s') % (label, s)
        self.status_message(msg)

    @QtCore.pyqtSlot(int)
    def _on_wood0(self, index):
        '''Handles changes in wood index 0'''
        if self.config.debug:
            print('_on_wood0', index)
        self._on_wood(0, index)

    @QtCore.pyqtSlot(int)
    def _on_wood1(self, index):
        '''Handles changes in wood index 1'''
        if self.config.debug:
            print('_on_wood1', index)
        self._on_wood(1, index)

    @QtCore.pyqtSlot(int)
    def _on_wood2(self, index):
        '''Handles changes in wood index 2'''
        if self.config.debug:
            print('_on_wood2', index)
        s = str(self.cb_wood[2].itemText(index))
        reinit = False
        if s == 'NONE':
            if self.boards[2].active:
                reinit = True
            i = self.cb_wood[3].findText('NONE')
            self.cb_wood[3].setCurrentIndex(i)
            self.cb_wood[3].setEnabled(False)
            self.boards[2].set_active(False)
            self.boards[3].set_active(False)
            self.le_boardm[0].setEnabled(False)
            self.le_boardm[1].setEnabled(False)
            self.le_boardm[0].setStyleSheet("color: gray;")
            self.le_boardm[1].setStyleSheet("color: gray;")
        else:
            if not self.boards[2].active:
                reinit = True
            self.cb_wood[3].setEnabled(True)
            self.boards[2].set_active(True)
            self.le_boardm[0].setEnabled(True)
            self.le_boardm[0].setStyleSheet("color: black;")
        self._on_wood(2, index, reinit)
        self.threeDS_enabler()

    @QtCore.pyqtSlot(int)
    def _on_wood3(self, index):
        '''Handles changes in wood index 3'''
        if self.config.debug:
            print('_on_wood3', index)
        s = str(self.cb_wood[3].itemText(index))
        reinit = False
        if s == 'NONE':
            if self.boards[3].active:
                reinit = True
            self.boards[3].set_active(False)
            self.le_boardm[1].setEnabled(False)
            self.le_boardm[1].setStyleSheet("color: gray;")
        else:
            if not self.boards[3].active:
                reinit = True
            self.boards[3].set_active(True)
            self.le_boardm[1].setEnabled(True)
            self.le_boardm[1].setStyleSheet("color: black;")
        self._on_wood(3, index, reinit)

    def _on_boardm(self, i):
        '''Handles changes board-M height changes'''
        if self.config.debug:
            print('_on_boardm', i)
        val = qt_utils.set_router_value(self.le_boardm[i], self.boards[i + 2], 'dheight',
                                        'set_height_from_string', bit=self.bit)
        if val is not None:
            self.reinit_spacing()
            self.draw()
            labels = ['Double', 'Double-Double']
            self.status_message(self.transl.tr(
                'Changed {} Board thickness to {}').format(labels[i], val))
            self.file_saved = False

    @QtCore.pyqtSlot()
    def _on_boardm0(self):
        '''Handles changes board-M0 height'''
        self._on_boardm(0)

    @QtCore.pyqtSlot()
    def _on_boardm1(self):
        '''Handles changes board-M1 height'''
        self._on_boardm(1)

    @QtCore.pyqtSlot()
    def _on_edit_undo(self):
        '''Handles undo event'''
        if self.config.debug:
            print('_on_edit_undo')
        self.spacing.undo()
        self.status_message('Undo')
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_moveL(self):
        '''Handles move left event'''
        if self.config.debug:
            print('_on_edit_moveL')
        (msg, warning) = self.spacing.cut_move_left()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_moveR(self):
        '''Handles move right event'''
        if self.config.debug:
            print('_on_edit_moveR')
        (msg, warning) = self.spacing.cut_move_right()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_widenL(self):
        '''Handles widen left event'''
        if self.config.debug:
            print('_on_edit_widenL')
        (msg, warning) = self.spacing.cut_widen_left()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_widenR(self):
        '''Handles widen right event'''
        if self.config.debug:
            print('_on_edit_widenR')
        (msg, warning) = self.spacing.cut_widen_right()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_trimL(self):
        '''Handles trim left event'''
        if self.config.debug:
            print('_on_edit_trimL')
        (msg, warning) = self.spacing.cut_trim_left()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_trimR(self):
        '''Handles trim right event'''
        if self.config.debug:
            print('_on_edit_trimR')
        (msg, warning) = self.spacing.cut_trim_right()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_toggle(self):
        '''Handles edit toggle event'''
        if self.config.debug:
            print('_on_edit_toggle')
        msg = self.spacing.cut_toggle()
        self.status_message(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_cursorL(self):
        '''Handles cursor left event'''
        if self.config.debug:
            print('_on_edit_cursorL')
        msg = self.spacing.cut_increment_cursor(-1)
        self.status_message(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_cursorR(self):
        '''Handles toggle right event'''
        if self.config.debug:
            print('_on_edit_cursorR')
        msg = self.spacing.cut_increment_cursor(1)
        self.status_message(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_activate_all(self):
        '''Handles edit activate all event'''
        if self.config.debug:
            print('_on_edit_activate_all')
        msg = self.spacing.cut_all_active()
        self.status_message(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_deactivate_all(self):
        '''Handles edit deactivate all event'''
        if self.config.debug:
            print('_on_edit_deactivate_all')
        msg = self.spacing.cut_all_not_active()
        self.status_message(msg)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_add(self):
        '''Handles add cut event'''
        if self.config.debug:
            print('_on_edit_add')
        (msg, warning) = self.spacing.cut_add()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_edit_del(self):
        '''Handles delete cuts event'''
        if self.config.debug:
            print('_on_edit_del')
        (msg, warning) = self.spacing.cut_delete_active()
        self.status_message(msg, warning)
        self.draw()

    @QtCore.pyqtSlot()
    def _on_flash_status_off(self):
        '''Handles event to turn off statusbar message'''
        if self.config.debug:
            print('_on_flash_status_off')
        self.status_message_label.setText('')

    @QtCore.pyqtSlot()
    def _on_fullscreen(self):
        '''Handles toggling full-screen mode'''
        if self.config.debug:
            print('_on_fullscreen')
        if self.windowState() & QtCore.Qt.WindowFullScreen:
            self.showNormal()
            self.status_message(self.transl.tr('Exited full-screen mode.'))
        else:
            self.showFullScreen()
            self.status_message(self.transl.tr('Entered full-screen mode.'))

    @QtCore.pyqtSlot()
    def _on_caul(self):
        '''Handles toggling showing caul template'''
        self.config.show_caul = self.caul_action.isChecked()
        if self.config_window is not None:
            self.config_window.update_state('show_caul')
        if self.config.show_caul:
            self.status_message(self.transl.tr('Turned on caul template.'))
        else:
            self.status_message(self.transl.tr('Turned off caul template.'))
        self.file_saved = False
        self.draw()

    @QtCore.pyqtSlot()
    def _on_finger_sizes(self):
        '''Handles toggling showing finger sizes'''
        if self.config.debug:
            print('_on_finger_sizes')
        self.config.show_finger_widths = self.finger_size_action.isChecked()
        if self.config_window is not None:
            self.config_window.update_state('show_finger_widths')
        if self.config.show_finger_widths:
            self.status_message(self.transl.tr('Turned on finger widths.'))
        else:
            self.status_message(self.transl.tr('Turned off finger widths.'))
        self.draw()

    @QtCore.pyqtSlot()
    def _on_fit(self):
        '''Handles toggling showing fit of joint'''
        self.config.show_fit = self.fit_action.isChecked()
        if self.config_window is not None:
            self.config_window.update_state('show_fit')
        if self.config.show_fit:
            self.status_message(self.transl.tr('Turned on fit view.'))
        else:
            self.status_message(self.transl.tr('Turned off fit view.'))
        self.file_saved = False
        self.draw()

    @QtCore.pyqtSlot()
    def _on_zoom(self):
        '''Handles toggling zoom mode'''
        self.fig.enable_zoom_mode(self.zoom_action.isChecked())
        if self.fig.zoom_mode:
            self.status_message(self.transl.tr('Turned on zoom mode.'))
        else:
            self.status_message(self.transl.tr('Turned off zoom mode.'))

    @QtCore.pyqtSlot()
    def _on_pass_id(self):
        '''Handles toggling showing router pass identifiers'''
        if self.config.debug:
            print('_on_pass_id')
        self.config.show_router_pass_identifiers = self.pass_id_action.isChecked()
        if self.config_window is not None:
            self.config_window.update_state('show_router_pass_identifiers')
        if self.config.show_router_pass_identifiers:
            self.status_message(self.transl.tr('Turned on router pass identifiers.'))
        else:
            self.status_message(self.transl.tr('Turned off router pass identifiers.'))
        self.draw()

    @QtCore.pyqtSlot()
    def _on_pass_location(self):
        '''Handles toggling showing router pass locations'''
        if self.config.debug:
            print('_on_pass_locations')
        self.config.show_router_pass_locations = self.pass_location_action.isChecked()
        if self.config_window is not None:
            self.config_window.update_state('show_router_pass_locations')
        if self.config.show_router_pass_locations:
            self.status_message(self.transl.tr('Turned on router pass locations.'))
        else:
            self.status_message(self.transl.tr('Turned off router pass locations.'))
        self.draw()

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
        # return if not in Editor spacing mode
        if self.tabs_spacing.currentIndex() != self.edit_spacing_id:
            event.ignore()
            return

        msg = None
        warning = False
        if event.key() == QtCore.Qt.Key_Control:
            self.control_key = True
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = True
        elif event.key() == QtCore.Qt.Key_U:
            self.spacing.undo()
            msg = 'Undo'
            self.draw()
        elif event.key() == QtCore.Qt.Key_A:
            msg = self.spacing.cut_all_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_N:
            msg = self.spacing.cut_all_not_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Return:
            msg = self.spacing.cut_toggle()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Minus:
            (msg, warning) = self.spacing.cut_delete_active()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Plus:
            (msg, warning) = self.spacing.cut_add()
            self.draw()
        elif event.key() == QtCore.Qt.Key_Left:
            if self.control_key and self.alt_key:
                (msg, warning) = self.spacing.cut_widen_left()
            elif self.control_key:
                (msg, warning) = self.spacing.cut_trim_left()
            elif self.alt_key:
                (msg, warning) = self.spacing.cut_move_left()
            else:
                msg = self.spacing.cut_increment_cursor(-1)
            self.draw()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.control_key and self.alt_key:
                (msg, warning) = self.spacing.cut_widen_right()
            elif self.control_key:
                (msg, warning) = self.spacing.cut_trim_right()
            elif self.alt_key:
                (msg, warning) = self.spacing.cut_move_right()
            else:
                msg = self.spacing.cut_increment_cursor(1)
            self.draw()
        else:
            msg = self.transl.tr('You pressed an unrecognized key: ')
            warning = True
            s = event.text()
            if s:
                msg += s
            else:
                msg += '%x' % event.key()
            event.ignore()
        if msg is not None:
            self.status_message(msg, warning)

    def keyReleaseEvent(self, event):
        '''
        Handles key release events
        '''
        # return if not edit spacing
        if self.tabs_spacing.currentIndex() != self.edit_spacing_id:
            event.ignore()
            return

        if event.key() == QtCore.Qt.Key_Control:
            self.control_key = False
        elif event.key() == QtCore.Qt.Key_Alt:
            self.alt_key = False
        else:
            event.ignore()
            if self.config.debug:
                print(self.transl.tr('you released %x') % event.key())


def run():
    '''
    Sets up and runs the application
    '''
    getcontext().prec = 4 + 4  # working in f8.4
    getcontext().Emin = -99999999  # working in f8.4
    getcontext().Emax = 99999999  # working in f8.4

#    QtGui.QApplication.setStyle('plastique')
#    QtGui.QApplication.setStyle('windows')
#    QtGui.QApplication.setStyle('windowsxp')
#    QtGui.QApplication.setStyle('macintosh')
#    QtGui.QApplication.setStyle('motif')
#    QtGui.QApplication.setStyle('cde')

    app = QtWidgets.QApplication(sys.argv)

    driver = Driver(app=app)
    driver.show()
    driver.center()
    driver.raise_()
    app.exec_()


if __name__ == '__main__':
    run()
