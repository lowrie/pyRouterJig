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
Tests for qt_driver
'''
from __future__ import print_function
from builtins import str

import sys
import unittest
from qt_driver import Driver
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtTest import QTest

app = QtGui.QApplication(sys.argv)

class Driver_Test(unittest.TestCase):
    '''
    Tests Driver
    '''
    def setUp(self):
        self.d = Driver()
        self.d.show()
        self.d.raise_()
        self.debug = self.d.config.debug
        QTest.qWaitForWindowShown(self.d)
    def test_options(self):
        self.assertFalse(self.debug)
    def test_defaults(self):
        self.assertEqual(str(self.d.le_board_width.text()), '7 1/2')
        self.assertEqual(str(self.d.le_bit_width.text()), '1/2')
        self.assertEqual(str(self.d.le_bit_depth.text()), '3/4')
        self.assertEqual(str(self.d.le_bit_angle.text()), '0')
    def screenshot(self, do_screenshot=True):
        QTest.qWaitForWindowShown(self.d)
        QTest.qWait(100)
        self.d._on_save(do_screenshot)
    def test_screenshots(self):
        # default
        print('************ default')
        self.d._on_fullscreen()
        self.screenshot()
        # default with caul
        print('************ caul')
        self.d._on_caul()
        self.screenshot()
        self.d._on_caul()
        # dovetail
        print('************ dovetail')
        self.d.le_bit_angle.clear()
        QTest.keyClicks(self.d.le_bit_angle, '7')
        self.d._on_bit_angle()
        self.assertEqual(str(self.d.le_bit_angle.text()), '7')
        self.screenshot()
        self.d.le_bit_angle.clear()
        QTest.keyClicks(self.d.le_bit_angle, '0')
        self.d._on_bit_angle()
        self.assertEqual(str(self.d.le_bit_angle.text()), '0')
        # Wood selection
        print('************ wood selection')
        for w in [0, 1]:
            i = self.d.cb_wood[w].findText('hard-maple')
            self.assertTrue(i >= 0)
            self.d.cb_wood[w].setCurrentIndex(i)
            self.d._on_wood(w)
        self.screenshot()
        for w in [0, 1]:
            i = self.d.cb_wood[w].findText('DiagCrossPattern')
            self.assertTrue(i >= 0)
            self.d.cb_wood[w].setCurrentIndex(i)
            self.d._on_wood(w)
        # spacing slider
        print('************ spacing slider')
        self.d.es_slider0.setValue(17)
        self.screenshot()
        self.d.es_slider0.setValue(0)
        # width slider
        print('************ width slider')
        self.d.es_slider1.setValue(27)
        self.screenshot()
        self.d.es_slider1.setValue(16)
        # centered checkbox
        print('************ centered checkbox')
        self.d.le_board_width.clear()
        QTest.keyClicks(self.d.le_board_width, '7')
        self.d._on_board_width()
        self.assertEqual(str(self.d.le_board_width.text()), '7')
        # mouseClick does work here:
#        QTest.mouseClick(self.d.cb_es_centered, QtCore.Qt.LeftButton)
#        self.d._on_cb_es_centered()
        self.d.cb_es_centered.setChecked(False)
        self.assertFalse(self.d.cb_es_centered.isChecked())
        self.screenshot()
        self.d.le_board_width.clear()
        QTest.keyClicks(self.d.le_board_width, '7 1/2')
        self.d._on_board_width()
        self.assertEqual(str(self.d.le_board_width.text()), '7 1/2')
        # ... but not here
#        QTest.mouseClick(self.d.cb_es_centered, QtCore.Qt.LeftButton)
#        self.d._on_cb_es_centered()
        self.d.cb_es_centered.setChecked(True)
        self.assertTrue(self.d.cb_es_centered.isChecked())
        # variable spacing
        print('************ variable spacing')
        self.d.tabs_spacing.setCurrentIndex(self.d.var_spacing_id)
        self.screenshot()
        # editor
        print('************ editor')
        self.d.tabs_spacing.setCurrentIndex(self.d.edit_spacing_id)
        QTest.keyClick(self.d.fig.canvas, QtCore.Qt.Key_Right)
        QTest.keyClick(self.d.fig.canvas, QtCore.Qt.Key_Return)
        QTest.keyClick(self.d.fig.canvas, QtCore.Qt.Key_Right)
        QTest.keyClick(self.d.fig.canvas, QtCore.Qt.Key_Return)
        self.screenshot()
        # double
        print('************ double')
        self.d.tabs_spacing.setCurrentIndex(self.d.equal_spacing_id)
        for w in [0, 1]:
            i = self.d.cb_wood[w].findText('hard-maple')
            self.assertTrue(i >= 0)
            self.d.cb_wood[w].setCurrentIndex(i)
            self.d._on_wood(w)
        i = self.d.cb_wood[2].findText('black-walnut')
        self.assertTrue(i >= 0)
        self.d.cb_wood[2].setCurrentIndex(i)
        self.d._on_wood2(i)
        self.screenshot()
        # double-double
        print('************ double-double')
        i = self.d.cb_wood[3].findText('mahogany')
        self.assertTrue(i >= 0)
        self.d.cb_wood[3].setCurrentIndex(i)
        self.d._on_wood3(i)
        self.screenshot()
        # save option
        print('************ save')
        self.screenshot(False)

if __name__ == '__main__':
    unittest.main()

