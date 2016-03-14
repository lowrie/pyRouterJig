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
import qt_utils

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
        title_label = QtGui.QLabel('<font color=blue><b>pyRouterJig Preferences</b></font>')
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

    def unit_string(self):
        if self.new_config['metric']:
            return 'mm'
        else:
            return 'in.'

    def create_units(self):
        '''Creates the layout for units preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        mesg = QtGui.QLabel('<font color=red><b>WARNING:</b></font>'
                            ' Changing any Units settings will require <i>pyRouterJig</i>'
                            ' to restart and your present joint will be lost.')
        mesg.setWordWrap(True)
        vbox.addWidget(mesg)

        hbox = QtGui.QHBoxLayout()
        self.cb_units = QtGui.QComboBox(self)
        self.cb_units.addItem('Metric')
        self.cb_units.addItem('English')
        self.cb_units.activated.connect(self._on_units)
        self.cb_units.setToolTip('The unit system.')
        hbox.addStretch(1)
        hbox.addWidget(self.cb_units)
        vbox.addLayout(hbox)

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

    def set_wood_combobox(self):
        (woods, patterns) = qt_utils.create_wood_dict(self.new_config['wood_images'])
        woodnames = woods.keys()
        woodnames.extend(patterns.keys())
        self.cb_wood.clear()
        self.cb_wood.addItems(woodnames)
        i = self.cb_wood.findText(self.new_config['default_wood'])
        if i < 0:
            self.cb_wood.setCurrentIndex(0)
            self.new_config['default_wood'] = self.cb_wood.currentText()
        else:
            self.cb_wood.setCurrentIndex(i)

    def create_boards(self):
        '''Creates the layout for boards preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.le_board_width_label = QtGui.QLabel('Initial Board Width ({}):'.format(self.unit_string()))
        self.le_board_width = QtGui.QLineEdit(w)
        self.le_board_width.setFixedWidth(self.line_edit_width)
        self.le_board_width.setText(str(self.config.board_width))
        self.le_board_width.editingFinished.connect(self._on_board_width)
        tt = 'The initial board width when pyRouterJig starts.'
        self.le_board_width_label.setToolTip(tt)
        self.le_board_width.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_board_width_label)
        hbox.addWidget(self.le_board_width)
        vbox.addLayout(hbox)

        self.le_db_thick_label = QtGui.QLabel('Initial Double Board Thickness ({}):'.format(self.unit_string()))
        self.le_db_thick = QtGui.QLineEdit(w)
        self.le_db_thick.setFixedWidth(self.line_edit_width)
        self.le_db_thick.setText(str(self.config.double_board_thickness))
        self.le_db_thick.editingFinished.connect(self._on_db_thick)
        tt = 'The initial double-board thickness when pyRouterJig starts.'
        self.le_db_thick_label.setToolTip(tt)
        self.le_db_thick.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_db_thick_label)
        hbox.addWidget(self.le_db_thick)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        (woods, patterns) = qt_utils.create_wood_dict(self.config.wood_images)
        woodnames = woods.keys()
        woodnames.extend(patterns.keys())
        self.cb_wood_label = QtGui.QLabel('Default Wood Fill:')
        self.cb_wood = QtGui.QComboBox(self)
        self.set_wood_combobox()
        self.cb_wood.activated.connect(self._on_wood)
        tt = 'The default wood fill for each board.'
        self.cb_wood.setToolTip(tt)
        self.cb_wood_label.setToolTip(tt)
        hbox.addWidget(self.cb_wood_label)
        hbox.addWidget(self.cb_wood)
        vbox.addLayout(hbox)

        self.le_wood_images_label = QtGui.QLabel('Wood Images Folder:')
        self.le_wood_images = QtGui.QLineEdit(w)
        self.le_wood_images.setText(str(self.config.wood_images))
        self.le_wood_images.editingFinished.connect(self._on_wood_images)
        tt = 'Location of wood images.'
        self.le_wood_images_label.setToolTip(tt)
        self.le_wood_images.setToolTip(tt)
        vbox.addWidget(self.le_wood_images_label)
        vbox.addWidget(self.le_wood_images)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_bit(self):
        '''Creates the layout for bit preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.le_bit_width_label = QtGui.QLabel('Initial Bit Width ({}):'.format(self.unit_string()))
        self.le_bit_width = QtGui.QLineEdit(w)
        self.le_bit_width.setFixedWidth(self.line_edit_width)
        self.le_bit_width.setText(str(self.config.bit_width))
        self.le_bit_width.editingFinished.connect(self._on_bit_width)
        tt = 'The initial bit width when pyRouterJig starts.'
        self.le_bit_width_label.setToolTip(tt)
        self.le_bit_width.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_bit_width_label)
        hbox.addWidget(self.le_bit_width)
        vbox.addLayout(hbox)

        self.le_bit_depth_label = QtGui.QLabel('Initial Bit Depth ({}):'.format(self.unit_string()))
        self.le_bit_depth = QtGui.QLineEdit(w)
        self.le_bit_depth.setFixedWidth(self.line_edit_width)
        self.le_bit_depth.setText(str(self.config.bit_depth))
        self.le_bit_depth.editingFinished.connect(self._on_bit_depth)
        tt = 'The initial bit depth when pyRouterJig starts.'
        self.le_bit_depth_label.setToolTip(tt)
        self.le_bit_depth.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_bit_depth_label)
        hbox.addWidget(self.le_bit_depth)
        vbox.addLayout(hbox)

        self.le_bit_angle_label = QtGui.QLabel('Initial Bit Angle (deg.):')
        self.le_bit_angle = QtGui.QLineEdit(w)
        self.le_bit_angle.setFixedWidth(self.line_edit_width)
        self.le_bit_angle.setText(str(self.config.bit_angle))
        self.le_bit_angle.editingFinished.connect(self._on_bit_angle)
        tt = 'The initial bit angle when pyRouterJig starts.'
        self.le_bit_angle_label.setToolTip(tt)
        self.le_bit_angle.setToolTip(tt)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.le_bit_angle_label)
        hbox.addWidget(self.le_bit_angle)
        vbox.addLayout(hbox)

        w.setLayout(vbox)
        return w

    def create_output(self):
        '''Creates the layout for output preferences'''
        w =  QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.cb_show_finger_widths = QtGui.QCheckBox('Show Finger Widths', w)
        self.cb_show_finger_widths.stateChanged.connect(self._on_show_finger_widths)
        self.cb_show_finger_widths.setToolTip('Display the width of each finger')
        vbox.addWidget(self.cb_show_finger_widths)

        self.cb_rpid = QtGui.QCheckBox('Show Router Pass Identifiers', w)
        self.cb_rpid.stateChanged.connect(self._on_rpid)
        self.cb_rpid.setToolTip('On each router pass, label its identifier')
        vbox.addWidget(self.cb_rpid)

        self.cb_rploc = QtGui.QCheckBox('Show Router Pass Locations', w)
        self.cb_rploc.stateChanged.connect(self._on_rploc)
        self.cb_rploc.setToolTip('On each router pass, label its distance from the right edge')
        vbox.addWidget(self.cb_rploc)

        self.le_printsf_label = QtGui.QLabel('Print Scale Factor:')
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

        self.le_min_image_label = QtGui.QLabel('Min Image Width:')
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

        self.le_max_image_label = QtGui.QLabel('Max Image Width:')
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
        self.cb_show_finger_widths.setChecked(self.config.show_finger_widths)
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
        label +=':'
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
    def _on_bit_width(self):
        if self.le_bit_width.isModified():
            s = str(self.le_bit_width.text())
            if self.units.valid_number(s):
                self.new_config['bit_width'] = s
                self.update_state('bit_width')
            else:
                msg = '"{}" is not a valid bit width'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_bit_width.setText(self.new_config['bit_width'])

    @QtCore.pyqtSlot()
    def _on_bit_depth(self):
        if self.le_bit_depth.isModified():
            s = str(self.le_bit_depth.text())
            if self.units.valid_number(s):
                self.new_config['bit_depth'] = s
                self.update_state('bit_depth')
            else:
                msg = '"{}" is not a valid bit depth'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_bit_depth.setText(self.new_config['bit_depth'])

    @QtCore.pyqtSlot()
    def _on_bit_angle(self):
        if self.le_bit_angle.isModified():
            s = str(self.le_bit_angle.text())
            if self.units.valid_number(s):
                self.new_config['bit_angle'] = s
                self.update_state('bit_angle')
            else:
                msg = '"{}" is not a valid bit angle'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_bit_angle.setText(self.new_config['bit_angle'])

    @QtCore.pyqtSlot()
    def _on_board_width(self):
        if self.le_board_width.isModified():
            s = str(self.le_board_width.text())
            if self.units.valid_number(s):
                self.new_config['board_width'] = s
                self.update_state('board_width')
            else:
                msg = '"{}" is not a valid board width'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_board_width.setText(self.new_config['board_width'])

    @QtCore.pyqtSlot()
    def _on_db_thick(self):
        if self.le_db_thick.isModified():
            s = str(self.le_db_thick.text())
            if self.units.valid_number(s):
                self.new_config['double_board_thickness'] = s
                self.update_state('double_board_thickness')
            else:
                msg = '"{}" is not a valid board width'.format(s)
                QtGui.QMessageBox.warning(self, 'Error', msg)
                self.le_db_thick.setText(self.new_config['double_board_thickness'])

    @QtCore.pyqtSlot(int)
    def _on_wood(self, index):
        s = str(self.cb_wood.itemText(index))
        if s != self.config.default_wood:
            self.new_config['default_wood'] = s
            self.update_state('default_wood')

    @QtCore.pyqtSlot()
    def _on_wood_images(self):
        if self.le_wood_images.isModified():
            text = str(self.le_wood_images.text())
            self.new_config['wood_images'] = text
            self.set_wood_combobox()
            self.update_state('wood_images')

    @QtCore.pyqtSlot()
    def _on_show_finger_widths(self):
        self.new_config['show_finger_widths'] = self.cb_show_finger_widths.isChecked()
        self.update_state('show_finger_widths')

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
