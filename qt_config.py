###########################################################################
#
# Copyright 2015-2016 Robert B. Lowrie (http://github.com/lowrie)
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
This module contains the Qt interface to setting config file parameters.
'''

import os, sys
from PyQt4 import QtCore, QtGui

import config_file

# Units
#   metric/english
#   num_increments
# Board
#   width
#   double_board_thickness
#   wood_images
#   default_wood
# Bit
#   width
#   depth
#   angle
# Output
#   background_color
#   -english_separator
#   -top_margin
#   -bottom_margin
#   -left_margin
#   -right_margin
#   -separation
#   -debug
# Tolerances
#   min_finger_width
#   caul_trim

class Config_Window(QtGui.QDialog):
    '''
    Qt interface to config file parameters
    '''
    def __init__(self, config, units, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.config = config
        self.new_config = config.__dict__.copy()
        self.units = units
        self.line_edit_width = 80
        title_label = QtGui.QLabel('<b>pyRouterJig Preferences</b>')
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(title_label)
        
        tabs = QtGui.QTabWidget()

        tabs.addTab(self.create_output(), 'Output')
        tabs.addTab(self.create_boards(), 'Boards')
        tabs.addTab(self.create_bit(), 'Bit')
        tabs.addTab(self.create_tolerances(), 'Tolerances')
        tabs.addTab(self.create_units(), 'Units')

        vbox.addWidget(tabs)
        vbox.addLayout(self.create_buttons())
        self.setLayout(vbox)
        self.initialize()
        self.change_state = 0

    def create_units(self):
        '''Creates the layout for units preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        mesg = QtGui.QLabel('Changing any Units settings will require pyRouterJig to restart and your present joint will be lost.')
        mesg.setWordWrap(True)
        vbox.addWidget(mesg)

        hbox = QtGui.QHBoxLayout()
        self.cb_units = QtGui.QComboBox(self)
        self.cb_units.addItem('Metric')
        self.cb_units.addItem('English')
        self.cb_units.activated.connect(self._on_units)
        self.cb_units.setToolTip('The unit system.')
        hbox.addWidget(self.cb_units)
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        #vbox.addWidget(self.cb_units)

        if self.config.metric:
            self.cb_units.setCurrentIndex(0)
        else:
            self.cb_units.setCurrentIndex(1)

        self.le_num_incr_label = QtGui.QLabel(self.units_label(self.config.metric))
        self.le_num_incr = QtGui.QLineEdit(w)
        self.le_num_incr.setFixedWidth(self.line_edit_width)
        self.le_num_incr.setText(str(self.config.num_increments))
        self.le_num_incr.editingFinished.connect(self._on_num_incr)
        tt = 'The number of increments per unit length.'
        self.le_num_incr.setToolTip(tt)
        self.le_num_incr_label.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_num_incr_label)
        hbox.addWidget(self.le_num_incr)
        vbox.addLayout(hbox)

        w.setLayout(vbox)
        return w

    def create_boards(self):
        '''Creates the layout for boards preferences'''
        w =  QtGui.QWidget()
        #w.setLayout(vbox)
        return w

    def create_bit(self):
        '''Creates the layout for bit preferences'''
        w =  QtGui.QWidget()
        #w.setLayout(vbox)
        return w

    def create_output(self):
        '''Creates the layout for output preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.cb_label_fingers = QtGui.QCheckBox('Label Fingers', w)
        self.cb_label_fingers.stateChanged.connect(self._on_label_fingers)
        self.cb_label_fingers.setToolTip('Display the width of each finger')
        vbox.addWidget(self.cb_label_fingers)

        self.cb_rpid = QtGui.QCheckBox('Label Router Pass Identifiers', w)
        self.cb_rpid.stateChanged.connect(self._on_rpid)
        self.cb_rpid.setToolTip('On each router pass, label its identifier')
        vbox.addWidget(self.cb_rpid)

        self.cb_rploc = QtGui.QCheckBox('Label Router Pass Locations', w)
        self.cb_rploc.stateChanged.connect(self._on_rploc)
        self.cb_rploc.setToolTip('On each router pass, label its distance from the right edge')
        vbox.addWidget(self.cb_rploc)

        self.le_printsf_label = QtGui.QLabel('Print Scale Factor')
        self.le_printsf = QtGui.QLineEdit(w)
        self.le_printsf.setFixedWidth(self.line_edit_width)
        self.le_printsf.setText(str(self.config.print_scale_factor))
        self.le_printsf.editingFinished.connect(self._on_printsf)
        tt = 'Scale output by this factor when printing.'
        self.le_printsf_label.setToolTip(tt)
        self.le_printsf.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_printsf_label)
        hbox.addWidget(self.le_printsf)
        vbox.addLayout(hbox)

        self.le_min_image_label = QtGui.QLabel('Min Image Width')
        self.le_min_image = QtGui.QLineEdit(w)
        self.le_min_image.setFixedWidth(self.line_edit_width)
        self.le_min_image.setText(str(self.config.min_image_width))
        self.le_min_image.editingFinished.connect(self._on_min_image)
        tt = 'On save image, minimum width of image in pixels.'
        self.le_min_image.setToolTip(tt)
        self.le_min_image_label.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_min_image_label)
        hbox.addWidget(self.le_min_image)
        vbox.addLayout(hbox)

        self.le_max_image_label = QtGui.QLabel('Max Image Width')
        self.le_max_image = QtGui.QLineEdit(w)
        self.le_max_image.setFixedWidth(self.line_edit_width)
        self.le_max_image.setText(str(self.config.max_image_width))
        self.le_max_image.editingFinished.connect(self._on_max_image)
        tt = 'On save image, maximum width of image in pixels.'
        self.le_max_image.setToolTip(tt)
        self.le_max_image_label.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_max_image_label)
        hbox.addWidget(self.le_max_image)
        vbox.addLayout(hbox)

        w.setLayout(vbox)
        return w

    def create_tolerances(self):
        '''Creates the layout for tolerances preferences'''
        w =  QtGui.QWidget()
        #w.setLayout(vbox)
        return w

    def create_buttons(self):
        '''Creates the layout for the buttons'''
        hbox_btns = QtGui.QHBoxLayout()
        
        btn_cancel = QtGui.QPushButton('Cancel', self)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_cancel.setAutoDefault(False)
        btn_cancel.setToolTip('Discard any preference changes and continue.')
        hbox_btns.addWidget(btn_cancel)
        
        self.btn_save = QtGui.QPushButton('Save', self)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setAutoDefault(False)
        self.btn_save.setEnabled(False)
        self.btn_save.setToolTip('Save preference changes permanently to your configuration file.')
        hbox_btns.addWidget(self.btn_save)
        return hbox_btns

    def initialize(self):
        '''
        Initializes certain widgets to their current values in the config object.
        We need this because these values may have changed in the config since
        the preferences window was created.
        '''
        self.cb_label_fingers.setChecked(self.config.label_fingers)
        self.cb_rpid.setChecked(self.config.show_router_pass_identifiers)
        self.cb_rploc.setChecked(self.config.show_router_pass_locations)

    def update_state(self, key, state=1):
        '''
        Updates the change state of the configuration
        '''
        if self.config.__dict__[key] != self.new_config[key]:
            self.change_state = max(state, self.change_state)
            self.btn_save.setEnabled(True)

    def units_label(self, metric):
        label = 'Increments per '
        if metric:
            label += 'mm'
        else:
            label += 'inch'
        return label

    @QtCore.pyqtSlot()
    def _on_cancel(self):
        '''
        Handles Cancel button events.
        '''
        self.close()

    @QtCore.pyqtSlot()
    def _on_save(self):
        '''
        Handles Save button events.
        '''
        do_save_config = False
        do_restart = False
        if self.change_state == 2:
            # Units were changes, so ask for a restart
            box = QtGui.QMessageBox(self)
            box.setTextFormat(QtCore.Qt.RichText)
            box.setIcon(QtGui.QMessageBox.NoIcon)
            box.setText('<font size=5 color=red>Warning!</font>')
            question = '<font size=5>You have changed a Units setting, which'\
                       ' requires <i>pyRouterJig</i> to restart to take effect.'\
                       ' Your current joint will be lost, unless you have already saved it. <p>'\
                       ' Press <b>Restart</b> to save the settings and restart.<p>'\
                       ' Press <b>Cancel</b> to discard the changes that you made.'\
                       ' </font>'
            box.setInformativeText(question)
            buttonRestart = box.addButton('Restart', QtGui.QMessageBox.AcceptRole)
            buttonCancel = box.addButton('Cancel', QtGui.QMessageBox.AcceptRole)
            box.setDefaultButton(buttonCancel)
            box.raise_()
            box.exec_()
            if box.clickedButton() == buttonRestart:
                do_save_config = True
                do_restart = True
        elif self.change_state == 1:
            # Units was not changed
            do_save_config = True
        if do_save_config:
            config_file.set_default_dimensions(self.new_config)
            self.config.__dict__.update(self.new_config)
            c = config_file.Configuration()
            c.write_config(self.new_config)
        if do_restart:
            os.execv(sys.argv[0], sys.argv)
        self.close()

    @QtCore.pyqtSlot(int)
    def _on_units(self, index):
        s = str(self.cb_units.itemText(index))
        metric = (s == 'Metric')
        if metric != self.config.metric:
            self.new_config['metric'] = metric
            self.update_state('metric', 2)
            if metric:
                 self.le_num_incr.setText('1')
            else:
                 self.le_num_incr.setText('32')
            self.le_num_incr_label.setText(self.units_label(metric))

    @QtCore.pyqtSlot()
    def _on_num_incr(self):
        if self.le_num_incr.isModified():
            text = str(self.le_num_incr.text())
            self.new_config['num_increments'] = int(text)
            self.update_state('num_increments', 2)

    @QtCore.pyqtSlot()
    def _on_label_fingers(self):
        self.new_config['label_fingers'] = self.cb_label_fingers.isChecked()
        self.update_state('label_fingers')

    @QtCore.pyqtSlot()
    def _on_rpid(self):
        self.new_config['show_router_pass_identifiers'] = self.cb_rpid.isChecked()
        self.update_state('show_router_pass_identifiers')

    @QtCore.pyqtSlot()
    def _on_rploc(self):
        self.new_config['show_router_pass_locations'] = self.cb_rploc.isChecked()
        self.update_state('show_router_pass_locations')

    @QtCore.pyqtSlot()
    def _on_printsf(self):
        if self.le_printsf.isModified():
            text = str(self.le_printsf.text())
            self.new_config['print_scale_factor'] = float(text)
            self.update_state('print_scale_factor')

    @QtCore.pyqtSlot()
    def _on_min_image(self):
        if self.le_min_image.isModified():
            text = str(self.le_min_image.text())
            self.new_config['min_image_width'] = int(text)
            self.change_state = max(1, self.change_state)
            self.update_state('min_image_width')

    @QtCore.pyqtSlot()
    def _on_max_image(self):
        if self.le_max_image.isModified():
            text = str(self.le_max_image.text())
            self.new_config['max_image_width'] = int(text)
            self.update_state('max_image_width')
