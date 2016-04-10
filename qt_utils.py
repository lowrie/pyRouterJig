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
Contains utilities for Qt functionality
'''
from __future__ import print_function
from future.utils import lrange

import os, glob

import utils
import router

from PyQt4 import QtCore, QtGui

def set_router_value(line_edit, obj, attr, setter, is_float=False, bit=None):
    # With editingFinished, we also need to check whether the
    # value actually changed. This is because editingFinished gets
    # triggered every time focus changes, which can occur many
    # times when an exception is thrown, or user tries to quit
    # in the middle of an exception, etc.  This logic also avoids
    # unnecessary redraws.
    if not line_edit.isModified():
        return None
    line_edit.setModified(False)
    text = str(line_edit.text())
    units = getattr(obj, 'units')
    try:
        # Call the appropriate setter function.  This is the function that will
        # throw an exception.
        if bit is None:
            getattr(obj, setter)(text)
        else:
            getattr(obj, setter)(bit, text)
        # Set the string value of the new value
        new_value = getattr(obj, attr)
        if is_float:
            text = str(new_value)
        else:
            text = units.increments_to_string(new_value)
        line_edit.setText(text)
        return text
    except router.Router_Exception as e:
        # Notify the user of the error, and set the line editor back to its
        # original value
        QtGui.QMessageBox.warning(line_edit.parentWidget(), 'Error', e.msg)
        old_value = getattr(obj, attr)
        text = units.increments_to_string(old_value)
        line_edit.setText(text)
        return None

class PreviewComboBox(QtGui.QComboBox):
    '''
    This comboxbox emits "activated" when hidePopup is called.  This allows
    for a combobox with a preview mode, so that as each selection is
    highlighted with the popup open, the figure can be updated.  Once the
    popup is closed, this hidePopup ensures that the figure is redrawn with
    the current actual selection.

    '''
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)

    def hidePopup(self):
        QtGui.QComboBox.hidePopup(self)
        #print('hidePopup')
        self.activated.emit(self.currentIndex())

class ShadowTextLineEdit(QtGui.QLineEdit):
    '''
    This line edit sets a grayed shadow text, until focus is received and text
    is entered.  Shadow text is the text displayed when the line edit is empty.
    '''
    def __init__(self, parent, shadow_text):
        QtGui.QLineEdit.__init__(self, parent)
        self.shadow_text = shadow_text
        self.initialize_shadow()

    def initialize_shadow(self):
        self.setText(self.shadow_text)
        self.setStyleSheet('color: gray;')
        self.has_real_text = False

    def focusInEvent(self, event):
        QtGui.QLineEdit.focusInEvent(self, event)
        # If no real text, clear the shadow text and darken the text
        if not self.has_real_text:
            self.clear()
            self.setStyleSheet('color: black;')

    def focusOutEvent(self, event):
        QtGui.QLineEdit.focusOutEvent(self, event)
        # If there's no text, set it back to the shadow
        if len(str(self.text())) == 0:
            self.initialize_shadow()
        else:
            self.has_real_text = True

def set_line_style(line):
    '''Sets the style for create_vline() and create_hline()'''
    line.setFrameShadow(QtGui.QFrame.Raised)
    line.setLineWidth(1)
    line.setMidLineWidth(1)
    line.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)

def create_vline():
    '''Creates a vertical line'''
    vline = QtGui.QFrame()
    vline.setFrameStyle(QtGui.QFrame.VLine)
    set_line_style(vline)
    return vline

def create_hline():
    '''Creates a horizontal line'''
    hline = QtGui.QFrame()
    hline.setFrameStyle(QtGui.QFrame.HLine)
    set_line_style(hline)
    return hline

def create_wood_dict(wood_images):
    '''
    Creates a dictionary {wood_name : wood_image_filename} by parsing the
    directory wood_images.  The wood_name is formed by taking the prefix of the
    wood_image_filename.
    '''
    # form woods dictionary, which is empty if wood_images directory does not exist
    woods = {}
    if os.path.isdir(wood_images):
        globber = os.path.join(wood_images, '*')
        files = glob.glob(globber)
        for f in files:
            name = os.path.basename(f)
            i = name.rfind('.')
            if i > 0:
                name = name[0:i]
            path = os.path.abspath(f)
            woods[name] = path
    # Set the available patterns
    patterns = {'DiagCrossPattern':QtCore.Qt.DiagCrossPattern,\
                'BDiagPattern':QtCore.Qt.BDiagPattern,\
                'FDiagPattern':QtCore.Qt.FDiagPattern,\
                'Dense1Pattern':QtCore.Qt.Dense1Pattern,\
                'Dense5Pattern':QtCore.Qt.Dense5Pattern,\
                'Solid Fill':QtCore.Qt.SolidPattern,\
                'No Fill':None}
    return (woods, patterns)
