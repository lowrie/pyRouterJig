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

import sys, traceback
import router
import mpl
import spacing
import utils
from options import OPTIONS
from doc import Doc

from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)

from PyQt4 import QtGui
from PyQt4 import QtCore
#from PySide import QtCore, QtGui

UNITS = OPTIONS['units']
DEBUG = OPTIONS['debug']

class Driver(QtGui.QMainWindow):
    '''
    Qt driver for MPL_Plotter
    '''
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        sys.excepthook = self.exception_hook
        self.except_handled = False

        # Create an initial joint
        self.board = router.Board(width=UNITS.inches_to_intervals(7.5))
        self.bit = router.Router_Bit(16, 24)
        self.template = router.Incra_Template(self.board)
        self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board)
        self.equal_spacing.set_cuts()
        self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
        self.var_spacing.set_cuts()
        self.spacing = self.equal_spacing # the default

        # Create the matplotlib object.  Nothing is drawn quite yet.
        self.mpl = mpl.MPL_Plotter()

        # Create the main frame and menus
        self.create_menu()
        self.create_status_bar()
        self.create_widgets()
        self.layout_widgets()

        # Draw the initial figure using matplotlib
        self.draw_mpl()

        # Keep track whether the current figure has been saved.  We initialize to true,
        # because we assume that that the user does not want the default joint saved.
        self.file_saved = True

    def exception_hook(self, etype, value, trace):
        '''
        Handler for all exceptions.
        '''
        if self.except_handled:
            return

        self.except_handled = True
        tmp = traceback.format_exception(etype, value, trace)
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

        self.file_menu = self.menubar.addMenu('pyRouterJig')

        about_action = QtGui.QAction(QtGui.QIcon('about.png'), '&About', self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip('About this program')
        about_action.triggered.connect(self._on_about)
        self.file_menu.addAction(about_action)

        save_action = QtGui.QAction(QtGui.QIcon('save.png'), '&Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save figure to file')
        save_action.triggered.connect(self._on_save)
        self.file_menu.addAction(save_action)

        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Quit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit pyRouterJig')
        exit_action.triggered.connect(self._on_exit)
        self.file_menu.addAction(exit_action)

    def create_widgets(self):
        '''
        Creates all of the widgets in the main panel
        '''
        self.main_frame = QtGui.QWidget()

        lineEditWidth = 80

        # Create the mpl Figure and FigureCanvas objects.
        self.dpi = 100
        self.canvas = FigureCanvas(self.mpl.fig)
        self.canvas.setParent(self.main_frame)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()

        # Board width text box
        self.tb_board_width_label = QtGui.QLabel('Board Width')
        self.tb_board_width = QtGui.QLineEdit(self.main_frame)
        self.tb_board_width.setFixedWidth(lineEditWidth)
        self.tb_board_width.setToolTip(Doc.board_width)
        self.tb_board_width.setText(UNITS.intervals_to_string(self.board.width))
        self.tb_board_width.editingFinished.connect(self._on_board_width)

        # Bit width text box
        self.tb_bit_width_label = QtGui.QLabel('Bit Width')
        self.tb_bit_width = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_width.setFixedWidth(lineEditWidth)
        self.tb_bit_width.setToolTip(Doc.bit_width)
        self.tb_bit_width.setText(UNITS.intervals_to_string(self.bit.width))
        self.tb_bit_width.editingFinished.connect(self._on_bit_width)

        # Bit depth text box
        self.tb_bit_depth_label = QtGui.QLabel('Bit Depth')
        self.tb_bit_depth = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_depth.setFixedWidth(lineEditWidth)
        self.tb_bit_depth.setToolTip(Doc.bit_depth)
        self.tb_bit_depth.setText(UNITS.intervals_to_string(self.bit.depth))
        self.tb_bit_depth.editingFinished.connect(self._on_bit_depth)

        # Bit angle text box
        self.tb_bit_angle_label = QtGui.QLabel('Bit Angle')
        self.tb_bit_angle = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_angle.setFixedWidth(lineEditWidth)
        self.tb_bit_angle.setToolTip(Doc.bit_angle)
        self.tb_bit_angle.setText('%g' % self.bit.angle)
        self.tb_bit_angle.editingFinished.connect(self._on_bit_angle)

        # Save button
        self.btn_save = QtGui.QPushButton('Save', self.main_frame)
        self.btn_save.setToolTip('Save figure to file.')
        self.btn_save.clicked.connect(self._on_save)

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
        self.es_slider0.setToolTip(Doc.es_slider0)
        if p.vMax - p.vMin < 10:
            self.es_slider0.setTickInterval(1)
        self.es_slider0.valueChanged.connect(self._on_es_slider0)

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
        self.es_slider1.setToolTip(Doc.es_slider1)
        if p.vMax - p.vMin < 10:
            self.es_slider1.setTickInterval(1)
        self.es_slider1.valueChanged.connect(self._on_es_slider1)

        # ...check box for centering
        p = params[2]
        self.es_cut_values[2] = p.vInit
        self.cb_es_centered = QtGui.QCheckBox(labels[2], self.main_frame)
        self.cb_es_centered.setChecked(True)
        self.cb_es_centered.stateChanged.connect(self._on_cb_es_centered)
        self.cb_es_centered.setToolTip(Doc.es_centered)

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
        self.vs_slider0.setToolTip(Doc.vs_slider0)
        if p.vMax - p.vMin < 10:
            self.vs_slider0.setTickInterval(1)
        self.vs_slider0.valueChanged.connect(self._on_vs_slider0)

    def layout_widgets(self):
        '''
        Does the layout of the widgets in the main frame
        '''

        # vbox contains all of the widgets in the main frame, positioned
        # vertically
        self.vbox = QtGui.QVBoxLayout()

        # Add the matplotlib canvas to the top
        self.vbox.addWidget(self.canvas)

        # hbox contains all of the control widgets
        # (everything but the canvas)
        self.hbox = QtGui.QHBoxLayout()

        # Add the board width label, board width input text box,
        # and save button, all stacked vertically on the left side.
        self.vbox_board_width = QtGui.QVBoxLayout()
        self.vbox_board_width.addWidget(self.tb_board_width_label)
        self.vbox_board_width.addWidget(self.tb_board_width)
        self.vbox_board_width.addStretch(1)
        self.vbox_board_width.addWidget(self.btn_save)
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

        # Add the spacing layouts as Tabs
        self.tabs_spacing = QtGui.QTabWidget()
        self.tab_es = QtGui.QWidget()
        self.tab_es.setLayout(self.hbox_es)
        self.tabs_spacing.addTab(self.tab_es, 'Equal')
        self.tab_vs = QtGui.QWidget()
        self.tab_vs.setLayout(self.hbox_vs)
        self.tabs_spacing.addTab(self.tab_vs, 'Variable')
        tip = 'These tabs specify the layout algorithm for the fingers.'
        self.tabs_spacing.setToolTip(tip)
        self.tabs_spacing.currentChanged.connect(self._on_tabs_spacing)

        # either add the spacing Tabs to the bottom
        #self.vbox.addLayout(self.hbox)
        #self.vbox.addWidget(self.tabs_spacing)
        # ... or to the right of the text boxes
        self.hbox.addWidget(self.tabs_spacing)
        self.vbox.addLayout(self.hbox)

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

    def draw_mpl(self):
        '''(Re)draws the matplotlib figure'''
        if DEBUG:
            print 'draw_mpl'
        self.template = router.Incra_Template(self.board)
        self.mpl.draw(self.template, self.board, self.bit, self.spacing)
        self.canvas.draw()
        self.canvas.update()

    def reinit_spacing(self):
        '''
        Re-initializes the joint spacing objects.  This must be called
        when the router bit or board change dimensions.
        '''

        # The ordering of the index is the same order that the tabs
        # were created in create main frame
        spacing_index = self.tabs_spacing.currentIndex()

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
            self.spacing = self.var_spacing
        else:
            raise ValueError('Bad value for spacing_index %d' % spacing_index)

    def _on_cb_es_centered(self):
        '''Handles changes to centered checkbox'''
        if DEBUG:
            print '_on_cb_es_centered'
        self.es_cut_values[2] = self.cb_es_centered.isChecked()
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.draw_mpl()
        if self.es_cut_values[2]:
            self.flash_status_message('Checked Centered.')
        else:
            self.flash_status_message('Unchecked Centered.')
        self.file_saved = False

    def _on_tabs_spacing(self, index):
        '''Handles changes to spacing algorithm'''
        if DEBUG:
            print '_on_tabs_spacing'
        self.reinit_spacing()
        self.draw_mpl()
        self.flash_status_message('Changed to spacing algorithm %s'\
                                  % str(self.tabs_spacing.tabText(index)))
        self.file_saved = False

    def _on_bit_width(self):
        '''Handles changes to bit width'''
        if DEBUG:
            print '_on_bit_width'
        # With editingFinished, we also need to check whether the
        # value actually changed. This is because editingFinished gets
        # triggered every time focus changes, which can occur many
        # times when an exception is thrown, or user tries to quit
        # in the middle of an exception, etc.  This logic also avoids
        # unnecessary redraws.
        if self.tb_bit_width.isModified():
            if DEBUG:
                print ' bit_width modified'
            self.tb_bit_width.setModified(False)
            text = str(self.tb_bit_width.text())
            self.bit.set_width_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed bit width to ' + text)
            self.file_saved = False

    def _on_bit_depth(self):
        '''Handles changes to bit depth'''
        if DEBUG:
            print '_on_bit_depth'
        if self.tb_bit_depth.isModified():
            self.tb_bit_depth.setModified(False)
            text = str(self.tb_bit_depth.text())
            self.bit.set_depth_from_string(text)
            self.draw_mpl()
            self.flash_status_message('Changed bit depth to ' + text)
            self.file_saved = False

    def _on_bit_angle(self):
        '''Handles changes to bit angle'''
        if DEBUG:
            print '_on_bit_angle'
        if self.tb_bit_angle.isModified():
            self.tb_bit_angle.setModified(False)
            text = str(self.tb_bit_angle.text())
            self.bit.set_angle_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed bit angle to ' + text)
            self.file_saved = False

    def _on_board_width(self):
        '''Handles changes to board width'''
        if DEBUG:
            print '_on_board_width'
        if self.tb_board_width.isModified():
            self.tb_board_width.setModified(False)
            text = str(self.tb_board_width.text())
            self.board.set_width_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed board width to ' + text)
            self.file_saved = False

    def _on_es_slider0(self, value):
        '''Handles changes to the equally-spaced slider B-spacing'''
        if DEBUG:
            print '_on_es_slider0', value
        self.es_cut_values[0] = value
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.es_slider0_label.setText(self.equal_spacing.full_labels[0])
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.es_slider0_label.text()))
        self.file_saved = False

    def _on_es_slider1(self, value):
        '''Handles changes to the equally-spaced slider Width'''
        if DEBUG:
            print '_on_es_slider1', value
        self.es_cut_values[1] = value
        self.equal_spacing.set_cuts(self.es_cut_values)
        self.es_slider1_label.setText(self.equal_spacing.full_labels[1])
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.es_slider1_label.text()))
        self.file_saved = False

    def _on_vs_slider0(self, value):
        '''Handles changes to the variable-spaced slider Fingers'''
        if DEBUG:
            print '_on_vs_slider0', value
        self.vs_cut_values[0] = value
        self.var_spacing.set_cuts(self.vs_cut_values)
        self.vs_slider0_label.setText(self.var_spacing.full_labels[0])
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.vs_slider0_label.text()))
        self.file_saved = False

    def _on_save(self):
        '''Handles save to file events'''
        if DEBUG:
            print '_on_save'

        # Limit file save types to png and pdf:
        #default = 'Portable Document Format (*.pdf)'
        #file_choices = 'PNG (*.png)'
        #file_choices += ';;' + default

        # Or, these wildcards match what matplotlib supports:
        filetypes = self.canvas.get_supported_filetypes_grouped()
        default_filetype = self.canvas.get_default_filetype()
        file_choices = ''
        for key, value in filetypes.iteritems():
            if len(file_choices) > 0:
                file_choices += ';;'
            # we probably need to consider all value, but for now, just
            # grab the first
            s = key + ' (*.' + value[0] + ')'
            file_choices += s
            if default_filetype == value[0]:
                default = s

        path = unicode(QtGui.QFileDialog.getSaveFileName(self,
                                                         'Save file', '',
                                                         file_choices, default))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
            self.file_saved = True
        else:
            self.flash_status_message("Unable to save %s!" % path)

    def _on_exit(self):
        '''Handles code exit events'''
        if DEBUG:
            print '_on_exit'
        if self.file_saved:
            QtGui.qApp.quit()
        else:
            msg = 'Figure was changed but not saved.  Are you sure to quit?'
            reply = QtGui.QMessageBox.question(self, 'Message', msg,
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                QtGui.qApp.quit()

    def _on_about(self):
        '''Handles about dialog event'''
        if DEBUG:
            print '_on_about'

        box = QtGui.QMessageBox(self)
        s = '<h2>Welcome to pyRouterJig!</h2>'
        s += '<h3>Version: %s</h3>' % utils.VERSION
        box.setText(s + Doc.short_desc + Doc.license)
        box.setTextFormat(QtCore.Qt.RichText)
        box.show()

    def flash_status_message(self, msg, flash_len_ms=None):
        '''Flashes a status message to the status bar'''
        self.statusbar.showMessage(msg)
        if flash_len_ms is not None:
            QtCore.QTimer.singleShot(flash_len_ms, self._on_flash_status_off)

    def _on_flash_status_off(self):
        '''Handles event to turn off statusbar message'''
        if DEBUG:
            print '_on_flash_status_off'
        self.statusbar.showMessage('')

    def closeEvent(self, event):
        '''
        For closeEvents (user closes window or presses Ctrl-Q), ignore and call
        _on_exit()
        '''
        if DEBUG:
            print 'closeEvent'
        self._on_exit()
        event.ignore()


def run():
    '''
    Sets up and runs the application
    '''
    Doc.set_statics()

    app = QtGui.QApplication(sys.argv)
    driver = Driver()
    driver.show()
    driver.raise_()
    app.exec_()

if __name__ == '__main__':
    run()

