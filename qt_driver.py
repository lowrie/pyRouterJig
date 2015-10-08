###########################################################################
#
# Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)
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
Contains the main driver, using pySlide or pyQt.
'''

import os, sys, traceback
import router
import mpl
import spacing
import utils
from utils import options

from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)

from PyQt4 import QtCore, QtGui
#from PySlide import QtCore, QtGui

class Driver(QtGui.QMainWindow):
    ''' Qt driver for MPL_Plotter
    '''
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        sys.excepthook = self.exception_hook
        self.except_handled = False

        # Create an initial joint
        self.board = router.Board(width=utils.inches_to_intervals(7.5))
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

        # Uncomment if you want the menu on the application window, for Mac OSX
#        if sys.platform=="darwin": 
#            self.menubar.setNativeMenuBar(False)1

        self.file_menu = self.menubar.addMenu('&pyRouterJig')

        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit pyRouterJig')
        exit_action.triggered.connect(self.on_exit)
        self.file_menu.addAction(exit_action)

        save_action = QtGui.QAction(QtGui.QIcon('save.png'), '&Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save figure to file')
        save_action.triggered.connect(self.on_save)
        self.file_menu.addAction(save_action)

        about_action = QtGui.QAction(QtGui.QIcon('about.png'), '&About', self)
        about_action.setShortcut('Ctrl+A')
        about_action.setStatusTip('About this program')
        about_action.triggered.connect(self.on_about)
        self.file_menu.addAction(about_action)

    def create_widgets(self):
        '''
        Creates all of the widgets in the main panel
        '''
        self.main_frame = QtGui.QWidget()

        lineEditWidth = 80
        sunits = options.units.units_string(verbose=True)
        
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
        tip = '<b>Board Width</b> is the width (in%s) of the board for the joint.' % sunits
        self.tb_board_width.setToolTip(tip)
        self.tb_board_width.setText(utils.intervals_to_string(self.board.width))
        self.tb_board_width.editingFinished.connect(self.on_board_width)
        
        # Bit width text box
        self.tb_bit_width_label = QtGui.QLabel('Bit Width')
        self.tb_bit_width = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_width.setFixedWidth(lineEditWidth)
        tip = '<b>Bit Width</b> is the width (in%s) of maximum cutting width of the router bit.' % sunits
        self.tb_bit_width.setToolTip(tip)
        self.tb_bit_width.setText(utils.intervals_to_string(self.bit.width))
        self.tb_bit_width.editingFinished.connect(self.on_bit_width)
        
        # Bit depth text box
        self.tb_bit_depth_label = QtGui.QLabel('Bit Depth')
        self.tb_bit_depth = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_depth.setFixedWidth(lineEditWidth)
        tip = '<b>Bit Depth</b> is the cutting depth (in%s) of the router bit.' % sunits
        self.tb_bit_depth.setToolTip(tip)
        self.tb_bit_depth.setText(utils.intervals_to_string(self.bit.depth))
        self.tb_bit_depth.editingFinished.connect(self.on_bit_depth)
        
        # Bit angle text box
        self.tb_bit_angle_label = QtGui.QLabel('Bit Angle')
        self.tb_bit_angle = QtGui.QLineEdit(self.main_frame)
        self.tb_bit_angle.setFixedWidth(lineEditWidth)
        tip = '<b>Bit Angle</b> is the angle (in degrees) of the router bit for dovetail bits.  Set to zero for straight bits.'
        self.tb_bit_angle.setToolTip(tip)
        self.tb_bit_angle.setText('%g' % self.bit.angle)
        self.tb_bit_angle.editingFinished.connect(self.on_bit_angle)

        # Save button
        self.btn_save = QtGui.QPushButton('Save', self.main_frame)
        self.btn_save.setToolTip('Save figure to file.')
        self.btn_save.clicked.connect(self.on_save)

        # Equal spacing widgets

        self.equal_spacing_params = self.equal_spacing.get_params()
        self.es_cut_values = [0] * 3

        # ...first slider
        p = self.equal_spacing_params[0]
        self.es_cut_values[0] = p.vInit
        self.es_slider0_label = QtGui.QLabel(p.label)
        self.es_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider0.setMinimum(p.vMin)
        self.es_slider0.setMaximum(p.vMax)
        self.es_slider0.setValue(p.vInit)
        self.es_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        tip = '<b>%s</b> slider allows you to specify additional spacing between the Board-B fingers' % p.label
        self.es_slider0.setToolTip(tip)
        if p.vMax - p.vMin < 10:
            self.es_slider0.setTickInterval(1)
        self.es_slider0.valueChanged.connect(self.on_es_slider0)

        # ...second slider
        p = self.equal_spacing_params[1]
        self.es_cut_values[1] = p.vInit
        self.es_slider1_label = QtGui.QLabel(p.label)
        self.es_slider1 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.es_slider1.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.es_slider1.setMinimum(p.vMin)
        self.es_slider1.setMaximum(p.vMax)
        self.es_slider1.setValue(p.vInit)
        self.es_slider1.setTickPosition(QtGui.QSlider.TicksBelow)
        tip = '<b>%s</b> slider allows you to specify additional width added to both Board-A and Board-B fingers.' % p.label
        self.es_slider1.setToolTip(tip)
        if p.vMax - p.vMin < 10:
            self.es_slider1.setTickInterval(1)
        self.es_slider1.valueChanged.connect(self.on_es_slider1)

        # ...check box for centering
        p = self.equal_spacing_params[2]
        self.es_cut_values[2] = p.vInit
        self.cb_es_centered = QtGui.QCheckBox(p.label, self.main_frame)
        self.cb_es_centered.setChecked(True)
        self.cb_es_centered.stateChanged.connect(self.on_cb_es_centered)
        tip = 'Check <b>%s</b> to force a finger to be centered on the board.' % p.label
        self.cb_es_centered.setToolTip(tip)

        # Variable spacing widgets
        
        self.var_spacing_params = self.var_spacing.get_params()
        self.vs_cut_values = [0] * 2

        # ...slider
        p = self.var_spacing_params[0]
        self.vs_cut_values[0] = p.vInit
        self.vs_slider0_label = QtGui.QLabel(p.label)
        self.vs_slider0 = QtGui.QSlider(QtCore.Qt.Horizontal, self.main_frame)
        self.vs_slider0.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.vs_slider0.setMinimum(p.vMin)
        self.vs_slider0.setMaximum(p.vMax)
        self.vs_slider0.setValue(p.vInit)
        self.vs_slider0.setTickPosition(QtGui.QSlider.TicksBelow)
        tip = '''<b>%s</b> slider allows you to specify the number of
        fingers.  At its minimum value, the width of the center finger is maximized. At
        its maximum value, the width of the center finger is minimized, and the result is
        the roughly the same as equally-spaced with, zero "B-spacing", zero "Width", and
        the "Centered" option checked.''' % p.label
        self.vs_slider0.setToolTip(tip)
        if p.vMax - p.vMin < 10:
            self.vs_slider0.setTickInterval(1)
        self.vs_slider0.valueChanged.connect(self.on_vs_slider0)

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
        self.tabs_spacing.currentChanged.connect(self.on_tabs_spacing)
        
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
        '''
        (Re)draws the matplotlib figure
        '''
        if options.debug: print 'draw_mpl'
        self.template = router.Incra_Template(self.board)
        self.mpl.draw(self.template, self.board, self.bit, self.spacing)
        self.canvas.draw()
        self.canvas.update()
    
    def on_cb_es_centered(self):
        if options.debug: print 'on_cb_es_centered'
        self.es_cut_values[2] = self.cb_es_centered.isChecked()
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        if self.es_cut_values[2]:
            self.flash_status_message('Checked Centered.')
        else:
            self.flash_status_message('Unchecked Centered.')

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
            self.equal_spacing_params = self.equal_spacing.get_params()
            p = self.equal_spacing_params[0]
            self.es_slider0.blockSignals(True)
            self.es_slider0.setMinimum(p.vMin)
            self.es_slider0.setMaximum(p.vMax)
            self.es_slider0.setValue(p.vInit)
            self.es_slider0.blockSignals(False)
            self.es_cut_values[0] = p.vInit
            p = self.equal_spacing_params[1]
            self.es_slider1.blockSignals(True)
            self.es_slider1.setMinimum(p.vMin)
            self.es_slider1.setMaximum(p.vMax)
            self.es_slider1.setValue(p.vInit)
            self.es_slider1.blockSignals(False)
            self.es_cut_values[1] = p.vInit
            p = self.equal_spacing_params[2]
            centered = self.es_cut_values[2]
            self.cb_es_centered.blockSignals(True)
            self.cb_es_centered.setChecked(centered)
            self.cb_es_centered.blockSignals(False)
            self.equal_spacing.set_cuts(values=self.es_cut_values)
            self.spacing = self.equal_spacing
        elif spacing_index == 1:
            # do the variable spacing parameters
            self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
            self.var_spacing_params = self.var_spacing.get_params()
            p = self.var_spacing_params[0]
            self.vs_slider0.blockSignals(True)
            self.vs_slider0.setMinimum(p.vMin)
            self.vs_slider0.setMaximum(p.vMax)
            self.vs_slider0.setValue(p.vInit)
            self.vs_slider0.blockSignals(False)
            self.vs_cut_values[0] = p.vInit
            self.var_spacing.set_cuts(values=self.vs_cut_values)
            self.spacing = self.var_spacing
        else:
            raise ValueError('Bad value for spacing_index %d' % spacing_index)

    def on_tabs_spacing(self, index):
        if options.debug: print 'on_tabs_spacing'
        self.reinit_spacing()
        self.draw_mpl()
        self.flash_status_message('Changed to spacing algorithm %s' % str(self.tabs_spacing.tabText(index)))
    
    def on_bit_width(self):
        if options.debug: print 'on_bit_width'
        # With editingFinished, we also need to check whether the
        # value actually changed. This is because editingFinished gets
        # triggered every time focus changes, which can occur many 
        # times when an exception is thrown, or user tries to quit
        # in the middle of an exception, etc.  This logic also avoids
        # unnecessary redraws.
        if self.tb_bit_width.isModified():
            if options.debug: print ' bit_width modified'
            self.tb_bit_width.setModified(False)
            text = str(self.tb_bit_width.text())
            self.bit.set_width_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed bit width to ' + text)
    
    def on_bit_depth(self):
        if options.debug: print 'on_bit_depth'
        if self.tb_bit_depth.isModified():
            self.tb_bit_depth.setModified(False)
            text = str(self.tb_bit_depth.text())
            self.bit.set_depth_from_string(text)
            self.draw_mpl()
            self.flash_status_message('Changed bit depth to ' + text)
    
    def on_bit_angle(self):
        if options.debug: print 'on_bit_angle'
        if self.tb_bit_angle.isModified():
            self.tb_bit_angle.setModified(False)
            text = str(self.tb_bit_angle.text())
            self.bit.set_angle_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed bit angle to ' + text)
    
    def on_board_width(self):
        if options.debug: print 'on_board_width'
        if self.tb_board_width.isModified():
            self.tb_board_width.setModified(False)
            text = str(self.tb_board_width.text())
            self.board.set_width_from_string(text)
            self.reinit_spacing()
            self.draw_mpl()
            self.flash_status_message('Changed board width to ' + text)

    def on_es_slider0(self, value):
        if options.debug: print 'on_es_slider0', value
        self.es_cut_values[0] = value
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.es_slider0_label.text()))
    
    def on_es_slider1(self, value):
        if options.debug: print 'on_es_slider1', value
        self.es_cut_values[1] = value
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.es_slider1_label.text()))
    
    def on_vs_slider0(self, value):
        if options.debug: print 'on_vs_slider0', value
        self.vs_cut_values[0] = value
        self.var_spacing.set_cuts(values=self.vs_cut_values)
        self.draw_mpl()
        self.flash_status_message('Changed slider %s' % str(self.vs_slider0_label.text()))

    def on_save(self, event):
        if options.debug: print 'on_save'

        # Limit file save types to png and pdf:
        #default = 'Portable Document Format (*.pdf)'
        #file_choices = 'PNG (*.png)'
        #file_choices += ';;' + default

        # Or, these wildcards match what matplotlib supports:
        filetypes = self.canvas.get_supported_filetypes_grouped()
        default_filetype = self.canvas.get_default_filetype()
        file_choices = ''
        for key, value in filetypes.iteritems():
            if len(file_choices) > 0: file_choices += ';;'
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
        else:
            self.flash_status_message("Unable to save %s!" % path)
        
    def on_exit(self):
        if options.debug: print 'on_exit'
        QtGui.qApp.quit()
        
    def on_about(self, event):
        if options.debug: print 'on_about'
        msg = 'pyRouterJig is a joint layout tool for woodworking.\n\n' +\
              'Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)\n\n' +\
               'pyRouterJig is free software: you can redistribute it and/or modify it under'+\
               ' the terms of the GNU General Public License as published by the Free Software'+\
               ' Foundation, either version 3 of the License, or (at your option) any later'+\
               ' version.\n\n' +\
               'pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY'+\
               ' WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR'+\
               ' A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\n\n'+\
               'You should have received a copy of the GNU General Public License along with'+\
               ' pyRouterJig; see the file LICENSE. If not, see http://www.gnu.org/licenses/.\n\n'+\
                   'USE AT YOUR OWN RISK!'

        QtGui.QMessageBox.about(self, 'About', msg)
    
    def flash_status_message(self, msg, flash_len_ms=None):
        self.statusbar.showMessage(msg)
        if flash_len_ms is not None:
            QtCore.QTimer.singleShot(flash_len_ms, self.on_flash_status_off)
    
    def on_flash_status_off(self):
        if options.debug: print 'on_flash_status_off'
        self.statusbar.showMessage('')


if __name__ == '__main__':

    # Uncomment this line for metric
    #options.units.metric = True

    #options.debug = True

    app = QtGui.QApplication(sys.argv)
    form = Driver()
    form.show()
    app.exec_()

