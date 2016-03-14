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

from PyQt4 import QtCore, QtGui

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
                'No fill':None}
    return (woods, patterns)
