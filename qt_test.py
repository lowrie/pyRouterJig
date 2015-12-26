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
from builtins import str

import sys
import unittest
import utils
from qt_driver import Driver
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtTest import QTest

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
    def test_screenshots(self):
        self.d._on_screenshot()
        self.d.le_bit_width.clear()
        QTest.keyClicks(self.d.le_bit_width, "1/4")
        QTest.keyPress(self.d.le_bit_width, QtCore.Qt.Key_Tab)
        self.d._on_bit_width()
        QTest.qWaitForWindowShown(self.d)
        QTest.qWait(1000)
        self.assertEqual(str(self.d.le_bit_width.text()), '1/4')
        self.d._on_screenshot()

if __name__ == '__main__':
    unittest.main()

