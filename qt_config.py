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
This module contains the Qt interface to setting config file parameters.
'''

import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import config_file
import qt_utils
import router


def form_line(label, widget=None, tooltip=None):
    '''
    Formats a line as
        label --------------- widget
    and returns the QLayout
    '''
    grid = QtWidgets.QGridLayout()
    line = qt_utils.create_hline()
    line.setMinimumWidth(20)
    if tooltip is not None:
        label.setToolTip(tooltip)
        if widget is not None:
            widget.setToolTip(tooltip)
        line.setToolTip(tooltip)
    grid.addWidget(label, 0, 0)
    grid.addWidget(line, 0, 1)
    if widget is not None:
        grid.addWidget(widget, 0, 2)
    grid.setColumnStretch(1, 5)
    return grid


def is_positive(v):
    '''
    Returns True if v is positive
    '''
    return v > 0


def is_nonnegative(v):
    '''
    Returns True if v is nonnegative
    '''
    return v >= 0


class Color_Button(QtWidgets.QPushButton):
    '''
    A QPushButton that is simply a rectangle of a single color.
    '''
    def __init__(self, color, parent):
        QtWidgets.QPushButton.__init__(self, parent)
        size = QtCore.QSize(80, 20)
        self.setFixedSize(size)
        self.set_color(color)

    def set_color(self, color):
        '''
        Sets the color of the button.
        '''
        c = QtGui.QColor(*color)
        self.setStyleSheet('QPushButton {{'
                           'border-width: 1px; '
                           'border-style: outset; '
                           'border-color: black; '
                           'background-color: rgba{}; }}'.format(c.getRgb()))


def add_color_to_dialog(color):
    '''
    Adds color to the QColorDialog custom colors.
    '''
    count = QtWidgets.QColorDialog.customCount()
    cprev = QtWidgets.QColorDialog.customColor(0)
    # shift all the current colors by one index
    for i in range(1, count):
        c = QtWidgets.QColorDialog.customColor(i)
        QtWidgets.QColorDialog.setCustomColor(i, cprev)
        cprev = c
    # add the new color to the first index
    QtWidgets.QColorDialog.setCustomColor(0, color)


class Misc_Value(object):
    '''
    Helper class to wrap dimensional values for use with qt_utils.set_router_value()
    '''
    def __init__(self, value, units, name, as_integer=True,
                 is_valid=is_positive):
        self.value = value
        self.units = units
        self.transl = units.transl
        self.name = name
        self.as_integer = as_integer
        self.is_valid = is_valid

    def set_value_from_string(self, s):
        '''
        Sets the value atrribute that is stored as a string in s
        '''
        msg = self.transl.tr('Unable to set {} to: {}<p>'\
              'Set to a positive number.').format(self.name, s)
        try:
            value = self.units.string_to_increments(s, self.as_integer)
        except:
            raise router.Router_Exception(msg)
        if not self.is_valid(value):
            raise router.Router_Exception(msg)
        self.value = value


class Config_Window(QtWidgets.QDialog):
    '''
    Qt interface to config file parameters
    '''
    def __init__(self, config, units, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.config = config
        self.new_config = self.config.__dict__.copy()
        self.line_edit_width = 80
        self.units = units
        self.transl = units.transl

        self.setWindowTitle(self.transl.tr('Settings'))

        # Form these objects so that we can do error checking on their changes
        bit_width = self.units.abstract_to_increments(self.config.bit_width)
        bit_depth = self.units.abstract_to_increments(self.config.bit_depth, False)
        bit_angle = self.units.abstract_to_float(self.config.bit_angle)
        bit_gentle = self.config.bit_gentle
        self.bit = router.Router_Bit(self.units, bit_width, bit_depth, bit_angle, bit_gentle)
        board_width = self.units.abstract_to_increments(self.config.board_width)
        self.board = router.Board(self.bit, width=board_width)

        # Form the tabs and their contents
        title_label = QtWidgets.QLabel(
            self.transl.tr('<font color=blue size=4><b>pyRouterJig Preferences</b></font>'))
        title_label.setAlignment(QtCore.Qt.AlignHCenter)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(title_label)

        tabs = QtWidgets.QTabWidget()

        tabs.addTab(self.create_output(), self.transl.tr('Output'))
        tabs.addTab(self.create_boards(), self.transl.tr('Boards'))
        tabs.addTab(self.create_bit(), self.transl.tr('Bit'))
        tabs.addTab(self.create_units(), self.transl.tr('Units'))
        tabs.addTab(self.create_colors(), self.transl.tr('Colors'))
        tabs.addTab(self.create_misc(), self.transl.tr('Misc'))

        vbox.addWidget(tabs)
        vbox.addLayout(self.create_buttons())
        self.setLayout(vbox)

        self.change_state = 0
        self.initialize()

    def create_units(self):
        '''Creates the layout for units preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        mesg = QtWidgets.QLabel(
            self.transl.tr('<font color=red><b>WARNING:</b></font>'
                           ' Changing any Units settings will require <i>pyRouterJig</i>'
                           ' to restart and your present joint will be lost.'))
        mesg.setWordWrap(True)
        vbox.addWidget(mesg)

        # Language block
        self.cb_lang_label = QtWidgets.QLabel(self.transl.tr('Language:'))
        self.cb_lang = QtWidgets.QComboBox(self)
        langs = qt_utils.create_lang_dict()
        for k in langs:
            self.cb_lang.addItem(k[0], k[1])
        i = self.cb_lang.findData(self.new_config['language'])
        # in case the language not found set the default one
        if i <= 0:
            i = self.cb_lang.findData('en_US')
        self.cb_lang.setCurrentIndex(i)
        self.cb_lang.activated.connect(self._on_lang)
        grid = form_line(self.cb_lang_label, self.cb_lang)
        vbox.addLayout(grid)

        # Units block
        self.cb_units_label = QtWidgets.QLabel(self.transl.tr('Unit System:'))
        self.cb_units = QtWidgets.QComboBox(self)
        self.cb_units.addItem(self.transl.tr('Metric'))
        self.cb_units.addItem(self.transl.tr('English'))
        self.cb_units.activated.connect(self._on_units)
        grid = form_line(self.cb_units_label, self.cb_units)
        vbox.addLayout(grid)

        self.le_num_incr_label = QtWidgets.QLabel(self.units_label(self.config.metric))
        self.le_num_incr = QtWidgets.QLineEdit(w)
        self.le_num_incr.setFixedWidth(self.line_edit_width)
        self.le_num_incr.editingFinished.connect(self._on_num_incr)
        tt = self.transl.tr('The number of increments per unit length.')
        grid = form_line(self.le_num_incr_label, self.le_num_incr, tt)

        # set same size for both combos
        size = self.cb_lang.size().width()
        self.cb_units.setFixedWidth(size)
        self.cb_lang.setFixedWidth(size)

        vbox.addLayout(grid)
        vbox.addStretch(1)
        w.setLayout(vbox)
        return w

    def set_wood_combobox(self):
        '''
        Sets the entries for the wood combox box, and resets the default wood.
        The wood names can be translated so we have use the value
        '''
        (woods, patterns) = qt_utils.create_wood_dict(self.new_config['wood_images'], self.transl)
        #woodnames = list(woods.keys())
        #woodnames.extend(patterns.keys())
        self.cb_wood.clear()
        #combo boxes now store values as well as keys
        skeys = sorted(woods.keys())
        for k in skeys:
            self.cb_wood.addItem(k, woods.get(k))
        # Next add patterns
        if skeys:
            self.cb_wood.insertSeparator(len(skeys))
        skeys = sorted(patterns.keys())
        for k in skeys:
            self.cb_wood.addItem(k, patterns.get(k))

        #i = self.cb_wood.findText(self.new_config['default_wood'])
        i = self.cb_wood.findData(self.new_config['default_wood'])
        if i < 0:
            self.cb_wood.setCurrentIndex(0)
            self.new_config['default_wood'] = self.cb_wood.currentData()
            # self.new_config['default_wood'] = str(self.cb_wood.currentText())
        else:
            self.cb_wood.setCurrentIndex(i)

    def create_boards(self):
        '''Creates the layout for boards preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        us = self.units.units_string(withParens=True)
        self.le_board_width_label = QtWidgets.QLabel(
            self.transl.tr('Initial Board Width{}:').format(us))
        self.le_board_width = QtWidgets.QLineEdit(w)
        self.le_board_width.setFixedWidth(self.line_edit_width)
        self.le_board_width.editingFinished.connect(self._on_board_width)
        tt = self.transl.tr('The initial board width when pyRouterJig starts.')
        grid = form_line(self.le_board_width_label, self.le_board_width, tt)
        vbox.addLayout(grid)

        self.le_db_thick_label = QtWidgets.QLabel(
            self.transl.tr('Initial Double Board Thickness{}:').format(us))
        self.le_db_thick = QtWidgets.QLineEdit(w)
        self.le_db_thick.setFixedWidth(self.line_edit_width)
        self.le_db_thick.editingFinished.connect(self._on_db_thick)
        tt = self.transl.tr('The initial double-board thickness when pyRouterJig starts.')
        grid = form_line(self.le_db_thick_label, self.le_db_thick, tt)
        vbox.addLayout(grid)

        (woods, patterns) = qt_utils.create_wood_dict(self.config.wood_images, self.transl)
        woodnames = list(woods.keys())
        woodnames.extend(patterns.keys())
        self.cb_wood_label = QtWidgets.QLabel(self.transl.tr('Default Wood Fill:'))
        self.cb_wood = QtWidgets.QComboBox(self)
        self.set_wood_combobox()
        self.cb_wood.activated.connect(self._on_wood)
        tt = self.transl.tr('The default wood fill for each board.')
        grid = form_line(self.cb_wood_label, self.cb_wood, tt)
        vbox.addLayout(grid)

        self.le_wood_images_label = QtWidgets.QLabel(self.transl.tr('Wood Images Folder:'))
        self.le_wood_images = QtWidgets.QLineEdit(w)
        self.le_wood_images.editingFinished.connect(self._on_wood_images)
        tt = self.transl.tr('Location of wood images.')
        self.le_wood_images.setToolTip(tt)
        grid = QtWidgets.QGridLayout()
        grid.addWidget(qt_utils.create_vline(), 0, 0, 4, 1)
        grid.addWidget(qt_utils.create_vline(), 0, 3, 4, 1)
        grid.addWidget(qt_utils.create_hline(), 0, 0, 1, 4)
        grid.addWidget(self.le_wood_images_label, 1, 1)
        grid.addWidget(self.le_wood_images, 2, 1)
        grid.addWidget(qt_utils.create_hline(), 3, 0, 1, 4)
        vbox.addLayout(grid)
        vbox.addWidget(self.le_wood_images)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_bit(self):
        '''Creates the layout for bit preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        us = self.units.units_string(withParens=True)
        self.le_bit_width_label = QtWidgets.QLabel(
            self.transl.tr('Initial Bit Width{}:').format(us))
        self.le_bit_width = QtWidgets.QLineEdit(w)
        self.le_bit_width.setFixedWidth(self.line_edit_width)
        self.le_bit_width.editingFinished.connect(self._on_bit_width)
        tt = self.transl.tr('The initial bit width when pyRouterJig starts.')
        grid = form_line(self.le_bit_width_label, self.le_bit_width, tt)
        vbox.addLayout(grid)

        self.le_bit_depth_label = QtWidgets.QLabel(
            self.transl.tr('Initial Bit Depth{}:').format(us))
        self.le_bit_depth = QtWidgets.QLineEdit(w)
        self.le_bit_depth.setFixedWidth(self.line_edit_width)
        self.le_bit_depth.editingFinished.connect(self._on_bit_depth)
        tt = self.transl.tr('The initial bit depth when pyRouterJig starts.')
        grid = form_line(self.le_bit_depth_label, self.le_bit_depth, tt)
        vbox.addLayout(grid)

        self.le_bit_angle_label = QtWidgets.QLabel(self.transl.tr('Initial Bit Angle (deg.):'))
        self.le_bit_angle = QtWidgets.QLineEdit(w)
        self.le_bit_angle.setFixedWidth(self.line_edit_width)
        self.le_bit_angle.editingFinished.connect(self._on_bit_angle)
        tt = self.transl.tr('The initial bit angle when pyRouterJig starts.')
        grid = form_line(self.le_bit_angle_label, self.le_bit_angle, tt)
        vbox.addLayout(grid)
        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_colors(self):
        '''Creates the layout for color preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        self.cb_print_color = QtWidgets.QCheckBox(self.transl.tr('Print in Color'), w)
        self.cb_print_color.stateChanged.connect(self._on_print_color)
        self.cb_print_color.setToolTip(
            self.transl.tr('If true, print in color.  Otherwise, converts to black and white.'))
        vbox.addWidget(self.cb_print_color)

        grid = QtWidgets.QGridLayout()
        flag_label = QtCore.Qt.AlignRight
        flag_color = QtCore.Qt.AlignLeft

        row = 0
        col = 0
        self.btn_canvas_background_label = QtWidgets.QLabel(self.transl.tr('Canvas Background'))
        self.btn_canvas_background = Color_Button(self.new_config['canvas_background'], w)
        self.btn_canvas_background.clicked.connect(
            lambda: self._on_set_color('canvas_background', self.btn_canvas_background))
        tt = self.transl.tr('Sets the background color of the canvas.')
        self.btn_canvas_background.setToolTip(tt)
        grid.addWidget(self.btn_canvas_background_label, row, col, flag_label)
        grid.addWidget(self.btn_canvas_background, row, col+1, flag_color)

        row += 1
        self.btn_canvas_foreground_label = QtWidgets.QLabel(self.transl.tr('Canvas Foreground'))
        self.btn_canvas_foreground = Color_Button(self.new_config['canvas_foreground'], w)
        self.btn_canvas_foreground.clicked.connect(
            lambda: self._on_set_color('canvas_foreground', self.btn_canvas_foreground))
        tt = self.transl.tr('Sets the foreground color of the canvas.')
        self.btn_canvas_foreground.setToolTip(tt)
        grid.addWidget(self.btn_canvas_foreground_label, row, col, flag_label)
        grid.addWidget(self.btn_canvas_foreground, row, col+1, flag_color)

        row += 1
        self.btn_board_background_label = QtWidgets.QLabel(self.transl.tr('Board Background'))
        self.btn_board_background = Color_Button(self.new_config['board_background'], w)
        self.btn_board_background.clicked.connect(
            lambda: self._on_set_color('board_background', self.btn_board_background))
        tt = self.transl.tr('Sets the top board background color.')
        self.btn_board_background.setToolTip(tt)
        grid.addWidget(self.btn_board_background_label, row, col, flag_label)
        grid.addWidget(self.btn_board_background, row, col+1, flag_color)

        row += 1
        self.btn_board_foreground_label = QtWidgets.QLabel(self.transl.tr('Board Foreground'))
        self.btn_board_foreground = Color_Button(self.new_config['board_foreground'], w)
        self.btn_board_foreground.clicked.connect(
            lambda: self._on_set_color('board_foreground', self.btn_board_foreground))
        tt = self.transl.tr('Sets the top board foreground color.')
        self.btn_board_foreground.setToolTip(tt)
        grid.addWidget(self.btn_board_foreground_label, row, col, flag_label)
        grid.addWidget(self.btn_board_foreground, row, col+1, flag_color)

        row = 0
        col += 2
        self.btn_pass_color_label = QtWidgets.QLabel(self.transl.tr('Pass'))
        self.btn_pass_color = Color_Button(self.new_config['pass_color'], w)
        self.btn_pass_color.clicked.connect(
            lambda: self._on_set_color('pass_color', self.btn_pass_color))
        tt = self.transl.tr('Sets the template foreground color for each pass.')
        self.btn_pass_color.setToolTip(tt)
        grid.addWidget(self.btn_pass_color_label, row, col, flag_label)
        grid.addWidget(self.btn_pass_color, row, col+1, flag_color)

        row += 1
        self.btn_pass_alt_color_label = QtWidgets.QLabel(self.transl.tr('Pass-Alt'))
        self.btn_pass_alt_color = Color_Button(self.new_config['pass_alt_color'], w)
        self.btn_pass_alt_color.clicked.connect(
            lambda: self._on_set_color('pass_alt_color', self.btn_pass_alt_color))
        tt = self.transl.tr('Sets the template foreground alternate color for each pass.')
        self.btn_pass_alt_color.setToolTip(tt)
        grid.addWidget(self.btn_pass_alt_color_label, row, col, flag_label)
        grid.addWidget(self.btn_pass_alt_color, row, col+1, flag_color)

        row += 1
        self.btn_center_color_label = QtWidgets.QLabel(self.transl.tr('Center Pass'))
        self.btn_center_color = Color_Button(self.new_config['center_color'], w)
        self.btn_center_color.clicked.connect(
            lambda: self._on_set_color('center_color', self.btn_center_color))
        tt = self.transl.tr('Sets the template foreground color for the center pass.')
        self.btn_center_color.setToolTip(tt)
        grid.addWidget(self.btn_center_color_label, row, col, flag_label)
        grid.addWidget(self.btn_center_color, row, col+1, flag_color)

        row += 1
        self.btn_watermark_color_label = QtWidgets.QLabel(self.transl.tr('Watermark'))
        self.btn_watermark_color = Color_Button(self.new_config['watermark_color'], w)
        self.btn_watermark_color.clicked.connect(
            lambda: self._on_set_color('watermark_color', self.btn_watermark_color))
        tt = self.transl.tr('Sets the watermark color.')
        self.btn_watermark_color.setToolTip(tt)
        grid.addWidget(self.btn_watermark_color_label, row, col, flag_label)
        grid.addWidget(self.btn_watermark_color, row, col+1, flag_color)

        vbox.addLayout(grid)
        grid = QtWidgets.QGridLayout()

        row = 0
        col = 0
        self.btn_template_margin_background_label = QtWidgets.QLabel(
            self.transl.tr('Template Margin Background'))
        self.btn_template_margin_background = Color_Button(
            self.new_config['template_margin_background'], w)
        self.btn_template_margin_background.clicked.connect(
            lambda: self._on_set_color('template_margin_background',
                                       self.btn_template_margin_background))
        tt = self.transl.tr('Sets the template margin background color.')
        self.btn_template_margin_background.setToolTip(tt)
        grid.addWidget(self.btn_template_margin_background_label, row, col, flag_label)
        grid.addWidget(self.btn_template_margin_background, row, col+1, flag_color)

        row += 1
        self.btn_template_margin_foreground_label = QtWidgets.QLabel(
            self.transl.tr('Template Margin Foreground'))
        self.btn_template_margin_foreground = Color_Button(
            self.new_config['template_margin_foreground'], w)
        self.btn_template_margin_foreground.clicked.connect(
            lambda: self._on_set_color('template_margin_foreground',
                                       self.btn_template_margin_foreground))
        tt = self.transl.tr('Sets the template margin foreground color.')
        self.btn_template_margin_foreground.setToolTip(tt)
        grid.addWidget(self.btn_template_margin_foreground_label, row, col, flag_label)
        grid.addWidget(self.btn_template_margin_foreground, row, col+1, flag_color)

        vbox.addLayout(grid)

        vbox.addStretch(1)
        w.setLayout(vbox)
        return w

    def create_output(self):
        '''Creates the layout for output preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        self.cb_show_caul = QtWidgets.QCheckBox(self.transl.tr('Show Caul Template'), w)
        self.cb_show_caul.stateChanged.connect(self._on_show_caul)
        self.cb_show_caul.setToolTip(self.transl.tr('Display the template for clamping cauls'))
        vbox.addWidget(self.cb_show_caul)

        self.cb_show_finger_widths = QtWidgets.QCheckBox(self.transl.tr('Show Finger Widths'), w)
        self.cb_show_finger_widths.stateChanged.connect(self._on_show_finger_widths)
        self.cb_show_finger_widths.setToolTip(self.transl.tr('Display the width of each finger'))
        vbox.addWidget(self.cb_show_finger_widths)

        self.cb_show_fit = QtWidgets.QCheckBox(self.transl.tr('Show Fit'), w)
        self.cb_show_fit.stateChanged.connect(self._on_show_fit)
        self.cb_show_fit.setToolTip(self.transl.tr('Display fit of joint'))
        vbox.addWidget(self.cb_show_fit)

        self.cb_rpid = QtWidgets.QCheckBox(self.transl.tr('Show Router Pass Identifiers'), w)
        self.cb_rpid.stateChanged.connect(self._on_rpid)
        self.cb_rpid.setToolTip(self.transl.tr('On each router pass, label its identifier'))
        vbox.addWidget(self.cb_rpid)

        self.cb_rploc = QtWidgets.QCheckBox(self.transl.tr('Show Router Pass Locations'), w)
        self.cb_rploc.stateChanged.connect(self._on_rploc)
        self.cb_rploc.setToolTip(
            self.transl.tr('On each router pass, label its distance from the right edge'))
        vbox.addWidget(self.cb_rploc)

        self.le_printsf_label = QtWidgets.QLabel(self.transl.tr('Print Scale Factor:'))
        self.le_printsf = QtWidgets.QLineEdit(w)
        self.le_printsf.setFixedWidth(self.line_edit_width)
        self.le_printsf.editingFinished.connect(self._on_printsf)
        tt = self.transl.tr('Scale output by this factor when printing.')
        grid = form_line(self.le_printsf_label, self.le_printsf, tt)
        vbox.addLayout(grid)

        self.le_linewidth_label = QtWidgets.QLabel(self.transl.tr('Line width:'))
        self.le_linewidth = QtWidgets.QLineEdit(w)
        self.le_linewidth.setFixedWidth(self.line_edit_width)
        self.le_linewidth.editingFinished.connect(self._on_line_width)
        tt = self.transl.tr('Line cut width.')
        grid = form_line(self.le_linewidth_label, self.le_linewidth, tt)
        vbox.addLayout(grid)

        self.le_min_image_label = QtWidgets.QLabel(self.transl.tr('Min Image Width (pixels):'))
        self.le_min_image = QtWidgets.QLineEdit(w)
        self.le_min_image.setFixedWidth(self.line_edit_width)
        self.le_min_image.editingFinished.connect(self._on_min_image)
        tt = self.transl.tr('On save image, minimum width of image or 0 for resolution.')
        grid = form_line(self.le_min_image_label, self.le_min_image, tt)
        vbox.addLayout(grid)

        self.le_max_image_label = QtWidgets.QLabel(self.transl.tr('Max Image Width (pixels):'))
        self.le_max_image = QtWidgets.QLineEdit(w)
        self.le_max_image.setFixedWidth(self.line_edit_width)
        self.le_max_image.editingFinished.connect(self._on_max_image)
        tt = self.transl.tr('On save image, maximum width of image or resolution.')
        grid = form_line(self.le_max_image_label, self.le_max_image, tt)
        vbox.addLayout(grid)

        w.setLayout(vbox)
        return w

    def create_misc(self):
        '''Creates the layout for misc preferences'''
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        us = self.units.units_string(withParens=True)

        self.le_min_finger_width_label = QtWidgets.QLabel(
            self.transl.tr('Min Finger Width{}:').format(us))
        self.le_min_finger_width = QtWidgets.QLineEdit(w)
        self.le_min_finger_width.setFixedWidth(self.line_edit_width)
        self.le_min_finger_width.editingFinished.connect(self._on_min_finger_width)
        tt = self.transl.tr('The minimum allowable finger width.'
                            '  Currently, only enforced for Equal Spacing.')
        grid = form_line(self.le_min_finger_width_label, self.le_min_finger_width, tt)
        vbox.addLayout(grid)

        self.le_caul_trim_label = QtWidgets.QLabel(self.transl.tr('Caul Trim{}:').format(us))
        self.le_caul_trim = QtWidgets.QLineEdit(w)
        self.le_caul_trim.setFixedWidth(self.line_edit_width)
        self.le_caul_trim.editingFinished.connect(self._on_caul_trim)
        tt = self.transl.tr('The distance from the edge of each finger'\
                                  ' to the edge of the corresponding caul finger.')
        grid = form_line(self.le_caul_trim_label, self.le_caul_trim, tt)
        vbox.addLayout(grid)

        self.le_warn_gap_label = QtWidgets.QLabel(self.transl.tr('Warning gap{}:').format(us))
        self.le_warn_gap = QtWidgets.QLineEdit(w)
        self.le_warn_gap.setFixedWidth(self.line_edit_width)
        self.le_warn_gap.editingFinished.connect(self._on_warn_gap)
        tt = self.transl.tr('If the gap in the joint exceeds this value, warn the user.')
        grid = form_line(self.le_warn_gap_label, self.le_warn_gap, tt)
        vbox.addLayout(grid)

        self.le_warn_overlap_label = QtWidgets.QLabel(
            self.transl.tr('Warning overlap{}:').format(us))
        self.le_warn_overlap = QtWidgets.QLineEdit(w)
        self.le_warn_overlap.setFixedWidth(self.line_edit_width)
        self.le_warn_overlap.editingFinished.connect(self._on_warn_overlap)
        tt = self.transl.tr('If the overlap in the joint exceeds this value, warn the user.')
        grid = form_line(self.le_warn_overlap_label, self.le_warn_overlap, tt)
        vbox.addLayout(grid)

        self.le_bit_gentle_label = QtWidgets.QLabel(self.transl.tr('Cut gentle (%):'))
        self.le_bit_gentle = QtWidgets.QLineEdit(w)
        self.le_bit_gentle.setFixedWidth(self.line_edit_width)
        self.le_bit_gentle.editingFinished.connect(self._on_bit_gentle_cut)
        tt = self.transl.tr('Cutting part of bit')
        grid = form_line(self.le_bit_gentle_label, self.le_bit_gentle, tt)
        vbox.addLayout(grid)

        vbox.addStretch(1)

        w.setLayout(vbox)
        return w

    def create_buttons(self):
        '''Creates the layout for the buttons'''
        hbox_btns = QtWidgets.QHBoxLayout()

        btn_cancel = QtWidgets.QPushButton(self.transl.tr('Cancel'), self)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_cancel.setAutoDefault(False)
        btn_cancel.setFocusPolicy(QtCore.Qt.ClickFocus)
        btn_cancel.setToolTip(self.transl.tr('Discard any preference changes and continue.'))
        hbox_btns.addWidget(btn_cancel)

        self.btn_save = QtWidgets.QPushButton(self.transl.tr('Save'), self)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setAutoDefault(False)
        self.btn_save.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.btn_save.setEnabled(False)
        self.btn_save.setToolTip(self.transl.tr(
            'Save preference changes permanently to your configuration file.'))
        hbox_btns.addWidget(self.btn_save)
        return hbox_btns

    def initialize(self):
        '''
        Initializes certain widgets to their current values in the config object.
        '''
        self.change_state_on_init = self.change_state

        if self.config.metric:
            self.cb_units.setCurrentIndex(0)
        else:
            self.cb_units.setCurrentIndex(1)

        self.le_num_incr.setText(str(self.config.num_increments))
        self.le_wood_images.setText(str(self.config.wood_images))
        self.cb_show_finger_widths.setChecked(self.config.show_finger_widths)
        self.cb_show_caul.setChecked(self.config.show_caul)
        self.cb_show_fit.setChecked(self.config.show_fit)
        self.cb_rpid.setChecked(self.config.show_router_pass_identifiers)
        self.cb_rploc.setChecked(self.config.show_router_pass_locations)
        self.cb_print_color.setChecked(self.config.print_color)
        self.le_printsf.setText(str(self.config.print_scale_factor))
        self.le_linewidth.setText(str(self.config.line_width))
        self.le_min_image.setText(str(self.config.min_image_width))
        self.le_max_image.setText(str(self.config.max_image_width))
        self.le_board_width.setText(str(self.config.board_width))
        self.le_db_thick.setText(str(self.config.double_board_thickness))
        self.le_bit_width.setText(str(self.config.bit_width))
        self.le_bit_depth.setText(str(self.config.bit_depth))
        self.le_bit_angle.setText(str(self.config.bit_angle))
        self.le_min_finger_width.setText(str(self.config.min_finger_width))
        self.le_caul_trim.setText(str(self.config.caul_trim))
        self.le_warn_gap.setText(str(self.config.warn_gap))
        self.le_warn_overlap.setText(str(self.config.warn_overlap))
        self.le_bit_gentle.setText(str(self.config.bit_gentle))
        self.set_wood_combobox()

    def update_state(self, key, state=1):
        '''
        Updates the change state of the configuration
        '''
        if self.config.__dict__[key] != self.new_config[key]:
            if self.config.debug:
                print('qt_config:update_state {} {}'.format(key, self.new_config[key]))
            self.change_state = max(state, self.change_state)
            self.btn_save.setEnabled(True)

    def units_label(self, metric):
        '''
        Returns a string "Increments per XX" where XX has the proper units.
        '''
        label = self.transl.tr('Increments per ')
        if metric:
            label += self.transl.tr('mm')
        else:
            label += self.transl.tr('inch')
        label += ':'
        return label

    @QtCore.pyqtSlot()
    def _on_cancel(self):
        '''
        Handles Cancel button events.
        '''
        if self.config.debug:
            print('qt_config:_on_cancel')
        self.setResult(0)
        # Set state back to the current configuration
        self.new_config = self.config.__dict__.copy()
        self.change_state = self.change_state_on_init
        self.close()

    @QtCore.pyqtSlot()
    def _on_save(self):
        '''
        Handles Save button events.
        '''
        if self.config.debug:
            print('qt_config:_on_save')
        do_save_config = False
        do_restart = False
        if self.change_state == 2:
            # Units were changes, so ask for a restart
            box = QtWidgets.QMessageBox(self)
            box.setTextFormat(QtCore.Qt.RichText)
            box.setIcon(QtWidgets.QMessageBox.NoIcon)
            box.setText(self.transl.tr('<font size=5 color=red>Warning!</font>'))
            question = self.transl.tr('<font size=5>You have changed a Units setting, which'\
                       ' requires <i>pyRouterJig</i> to restart to take effect.'\
                       ' Your current joint will be lost, unless you have already saved it. <p>'\
                       ' Press <b>Restart</b> to save the settings and restart.<p>'\
                       ' Press <b>Cancel</b> to discard the changes to preferences that'\
                       ' you have made.</font>')
            box.setInformativeText(question)
            buttonRestart = box.addButton(self.transl.tr('Restart'),
                                          QtWidgets.QMessageBox.AcceptRole)
            buttonCancel = box.addButton(self.transl.tr('Cancel'),
                                         QtWidgets.QMessageBox.AcceptRole)
            box.setDefaultButton(buttonCancel)
            box.raise_()
            box.exec_()
            if box.clickedButton() == buttonRestart:
                do_save_config = True
                do_restart = True
                if self.new_config['metric'] != self.config.metric:
                    config_file.set_default_dimensions(self.new_config)
            else:
                self._on_cancel()
        elif self.change_state == 1:
            # Units were not changed
            do_save_config = True
        if do_save_config:
            self.config.__dict__.update(self.new_config)
            c = config_file.Configuration()
            c.write_config(self.new_config)
        if do_restart:
            os.execv(sys.argv[0], sys.argv)
        self.setResult(1)
        self.change_state = 0
        self.btn_save.setEnabled(False)
        self.close()

    def closeEvent(self, event):
        '''
        This is called on save, cancel, and if user closes the window.
        '''
        if self.config.debug:
            print('qt_config:closeEvent')
        self.btn_save.setEnabled(self.change_state > 0)

    @QtCore.pyqtSlot(int)
    def _on_units(self, index):
        '''
        Handles change in units
        '''
        if self.config.debug:
            print('qt_config:_on_units', index)
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

    @QtCore.pyqtSlot(int)
    def _on_lang(self, index):
        '''
        Handles change in language
        '''
        if self.config.debug:
            print('qt_config:_on_lang', index, str(self.cb_lang.itemData(index)))
        self.new_config['language'] = str(self.cb_lang.itemData(index))
        self.update_state('language', 2)

    @QtCore.pyqtSlot()
    def _on_num_incr(self):
        '''
        Handles change in number of increments
        '''
        if self.config.debug:
            print('qt_config:_on_num_incr')
        if self.le_num_incr.isModified():
            text = str(self.le_num_incr.text())
            self.new_config['num_increments'] = int(text)
            self.update_state('num_increments', 2)

    @QtCore.pyqtSlot()
    def _on_bit_width(self):
        '''
        Handles change in bit width
        '''
        if self.config.debug:
            print('qt_config:_on_bit_width')
        val = qt_utils.set_router_value(self.le_bit_width, self.bit, 'width',
                                        'set_width_from_string')
        if val is not None:
            self.new_config['bit_width'] = val
            self.update_state('bit_width')

    @QtCore.pyqtSlot()
    def _on_bit_depth(self):
        '''
        Handles change in bit depth
        '''
        if self.config.debug:
            print('qt_config:_on_bit_depth')
        val = qt_utils.set_router_value(self.le_bit_depth, self.bit, 'depth',
                                        'set_depth_from_string')
        if val is not None:
            self.new_config['bit_depth'] = val
            self.update_state('bit_depth')

    @QtCore.pyqtSlot()
    def _on_bit_angle(self):
        '''
        Handles change in bit angle
        '''
        if self.config.debug:
            print('qt_config:_on_bit_angle')
        val = qt_utils.set_router_value(self.le_bit_angle, self.bit, 'angle',
                                        'set_angle_from_string', True)
        if val is not None:
            self.new_config['bit_angle'] = val
            self.update_state('bit_angle')

    @QtCore.pyqtSlot()
    def _on_board_width(self):
        '''
        Handles change in board width
        '''
        if self.config.debug:
            print('qt_config:_on_board_width')
        val = qt_utils.set_router_value(self.le_board_width, self.board, 'width',
                                        'set_width_from_string')
        if val is not None:
            self.new_config['board_width'] = val
            self.update_state('board_width')

    @QtCore.pyqtSlot()
    def _on_db_thick(self):
        '''
        Handles change in double board thickness
        '''
        if self.config.debug:
            print('qt_config:_on_db_thick')
        val = qt_utils.set_router_value(self.le_db_thick, self.board, 'dheight',
                                        'set_height_from_string', bit=self.bit)
        if val is not None:
            self.new_config['double_board_thickness'] = val
            self.update_state('double_board_thickness')

    @QtCore.pyqtSlot(int)
    def _on_wood(self, index):
        '''
        Handles change in wood
        '''
        if self.config.debug:
            print('qt_config:_on_wood', index)
        s = self.cb_wood.currentData()
        if s != self.config.default_wood:
            self.new_config['default_wood'] = s
            self.update_state('default_wood')

    @QtCore.pyqtSlot()
    def _on_wood_images(self):
        '''
        Handles change in wood image
        '''
        if self.config.debug:
            print('qt_config:_on_wood_images')
        if self.le_wood_images.isModified():
            text = str(self.le_wood_images.text())
            self.new_config['wood_images'] = text
            self.set_wood_combobox()
            self.update_state('wood_images')

    @QtCore.pyqtSlot()
    def _on_print_color(self):
        '''
        Handles change in print color
        '''
        if self.config.debug:
            print('qt_config:_on_print_color')
        self.new_config['print_color'] = self.cb_print_color.isChecked()
        self.update_state('print_color')

    @QtCore.pyqtSlot()
    def _on_show_finger_widths(self):
        '''
        Handles change in showing finger widths
        '''
        if self.config.debug:
            print('qt_config:_on_show_finger_widths')
        self.new_config['show_finger_widths'] = self.cb_show_finger_widths.isChecked()
        self.update_state('show_finger_widths')

    @QtCore.pyqtSlot()
    def _on_show_caul(self):
        '''
        Handles change in showing caul
        '''
        if self.config.debug:
            print('qt_config:_on_show_caul')
        self.new_config['show_caul'] = self.cb_show_caul.isChecked()
        self.update_state('show_caul')

    @QtCore.pyqtSlot()
    def _on_show_fit(self):
        '''
        Handles change in showing fit
        '''
        if self.config.debug:
            print('qt_config:_on_show_fit')
        self.new_config['show_fit'] = self.cb_show_fit.isChecked()
        self.update_state('show_fit')

    @QtCore.pyqtSlot()
    def _on_rpid(self):
        '''
        Handles change in showing the router pass identifiers
        '''
        if self.config.debug:
            print('qt_config:_on_rpid')
        self.new_config['show_router_pass_identifiers'] = self.cb_rpid.isChecked()
        self.update_state('show_router_pass_identifiers')

    @QtCore.pyqtSlot()
    def _on_rploc(self):
        '''
        Handles change in router pass locations
        '''
        if self.config.debug:
            print('qt_config:_on_rploc')
        self.new_config['show_router_pass_locations'] = self.cb_rploc.isChecked()
        self.update_state('show_router_pass_locations')

    @QtCore.pyqtSlot()
    def _on_printsf(self):
        '''
        Handles change in print scale factor
        '''
        if self.config.debug:
            print('qt_config:_on_printsf')
        if self.le_printsf.isModified():
            if self.config.debug:
                print('  _on_printsf modified')
            self.le_printsf.setModified(False)
            s = str(self.le_printsf.text())
            ok = True
            try:
                new_value = float(s)
                if new_value <= 0:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['print_scale_factor'] = float(s)
                self.update_state('print_scale_factor')
            else:
                msg = self.transl.tr('Unable to set Print Scale Factor to: {}<p>'\
                      'Set to a positive number.').format(s)
                QtWidgets.QMessageBox.warning(self, self.transl.tr('Error'), msg)
                self.le_printsf.setText(str(self.new_config['print_scale_factor']))

    @QtCore.pyqtSlot()
    def _on_line_width(self):
        '''
        Handles change in print scale factor
        '''
        if self.config.debug:
            print('qt_config:_on_line_width')

        if self.le_linewidth.isModified():
            if self.config.debug:
                print('  _on_line_width modified')
            self.le_printsf.setModified(False)
            s = str(self.le_linewidth.text())
            ok = True
            try:
                new_value = float(s)
                if new_value < 0 or new_value > 2:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['line_width'] = float(s)
                self.update_state('line_width')
            else:
                msg = self.transl.tr('Unable to set Line Width to: {}<p>'\
                      'Set to a positive number.').format(s)
                QtWidgets.QMessageBox.warning(self, self.transl.tr('Error'), msg)
                self.le_printsf.setText(str(self.new_config['line_width']))

    @QtCore.pyqtSlot()
    def _on_min_image(self):
        '''
        Handles change in min image width
        '''
        if self.config.debug:
            print('qt_config:_on_min_image')
        if self.le_min_image.isModified():
            self.le_min_image.setModified(False)
            s = str(self.le_min_image.text())
            ok = True
            try:
                new_value = int(s)
                if new_value < 0:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['min_image_width'] = int(s)
                self.update_state('min_image_width')

                if int(s) > 0:
                    self.le_min_image_label = QtWidgets.QLabel(self.transl.tr('Min Image Width (pixels):'))
                    self.le_max_image_label.setText(self.transl.tr('Max Image Width (pixels):'))
                else:
                    self.le_min_image_label = QtWidgets.QLabel(self.transl.tr('DPI mode (0):'))
                    self.le_max_image_label.setText(self.transl.tr('Image resolution (ppi):'))
            else:
                msg = self.transl.tr('Unable to set Min Image Width to: {}<p>'\
                      'Set to a positive integer.').format(s)
                QtWidgets.QMessageBox.warning(self, 'Error', msg)
                self.le_min_image.setText(str(self.new_config['min_image_width']))

    @QtCore.pyqtSlot()
    def _on_max_image(self):
        '''
        Handles change in max image width
        '''
        if self.config.debug:
            print('qt_config:_on_max_image')
        if self.le_max_image.isModified():
            self.le_max_image.setModified(False)
            s = str(self.le_max_image.text())
            ok = True
            min_value = int(self.new_config['min_image_width'])
            try:
                new_value = int(s)
                if new_value <= min_value:
                    ok = False
            except:
                ok = False
            if ok:
                self.new_config['max_image_width'] = int(s)
                self.update_state('max_image_width')
            else:
                msg = self.transl.tr('Unable to set Max Image Width to: {}<p>'\
                      'Set to a positive integer >= Min Image Width ({})').format(s, min_value)
                QtWidgets.QMessageBox.warning(self, 'Error', msg)
                self.le_max_image.setText(str(self.new_config['max_image_width']))

    @QtCore.pyqtSlot()
    def _on_min_finger_width(self):
        '''
        Handles change in min finger width
        '''
        if self.config.debug:
            print('qt_config:_on_min_finger_width')
        i = self.units.abstract_to_increments(self.new_config['min_finger_width'])
        v = Misc_Value(i, self.units, 'Min Finger Width')
        val = qt_utils.set_router_value(self.le_min_finger_width, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['min_finger_width'] = val
            self.update_state('min_finger_width')

    @QtCore.pyqtSlot()
    def _on_caul_trim(self):
        '''
        Handles change in caul trim
        '''
        if self.config.debug:
            print('qt_config:_on_caul_trim')
        i = self.units.abstract_to_increments(self.new_config['caul_trim'])
        v = Misc_Value(i, self.units, 'Caul Trim')
        val = qt_utils.set_router_value(self.le_caul_trim, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['caul_trim'] = val
            self.update_state('caul_trim')

    @QtCore.pyqtSlot()
    def _on_warn_gap(self):
        '''
        Handles change in gap that shows a warning
        '''
        if self.config.debug:
            print('qt_config:_on_warn_gap')
        i = self.units.abstract_to_increments(self.new_config['warn_gap'])
        v = Misc_Value(i, self.units, 'Warning Overlap', False,
                       is_nonnegative)
        val = qt_utils.set_router_value(self.le_warn_gap, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['warn_gap'] = val
            self.update_state('warn_gap')

    @QtCore.pyqtSlot()
    def _on_warn_overlap(self):
        '''
        Handles change in overlap that shows a warning
        '''
        if self.config.debug:
            print('qt_config:_on_warn_overlap')
        i = self.units.abstract_to_increments(self.new_config['warn_overlap'])
        v = Misc_Value(i, self.units, 'Warning Overlap', False,
                       is_nonnegative)
        val = qt_utils.set_router_value(self.le_warn_overlap, v, 'value',
                                        'set_value_from_string')
        if val is not None:
            self.new_config['warn_overlap'] = val
            self.update_state('warn_overlap')

    @QtCore.pyqtSlot()
    def _on_bit_gentle_cut(self):
        '''
        Handles change in bit gentle
        '''
        if self.config.debug:
            print('qt_config:_on_gentle_cut')
        val = qt_utils.set_router_value(self.le_bit_gentle, self.bit, 'bit_gentle',
                                        'set_gentle_from_string', True)

        if val is not None:
            self.new_config['bit_gentle'] = val
            self.update_state('bit_gentle')

    @QtCore.pyqtSlot(str, Color_Button)
    def _on_set_color(self, name, btn):
        '''
        Handles change in color
        '''
        if self.config.debug:
            print('qt_config:set_color {}'.format(name))
        init_color = QtGui.QColor(*self.new_config[name])
        flags = QtWidgets.QColorDialog.ShowAlphaChannel | QtWidgets.QColorDialog.DontUseNativeDialog
        color = QtWidgets.QColorDialog.getColor(init_color, self, 'Select {}'.format(name), flags)
        if color.isValid():
            self.new_config[name] = color.getRgb()
            self.update_state(name)
            btn.set_color(self.new_config[name])
            add_color_to_dialog(color)
