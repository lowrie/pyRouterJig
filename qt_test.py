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
import utils
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtTest import QTest

app = QtWidgets.QApplication(sys.argv)

class Case(object):
    def __init__(self, angle, width, depth, spacing, board_width=7):
        self.width = width
        self.depth = depth
        self.angle = angle
        self.spacing = spacing
        self.board_width = board_width

# These cases are the dovetails in the Incra Master Guide.  The spacing argument is what the
# Guide recommends.
cases = [Case(7  , '3/4' , '3/4' , 1.3125),
         Case(7  , '3/4' , '1/2' , 1.375),
         Case(7  , '5/8' , '3/4' , 1.0625),
         Case(7  , '5/8' , '1/2' , 1.125),
         Case(14 , '1/2' , '3/8' , .8125),
         Case(14 , '1/2' , '1/4' , .875),
         Case(10 , '1/2' , '1/2' , .8125),
         Case(9  , '3/8' , '1/4' , .6875),
         Case(9  , '5/16', '3/16', .5625),
         Case(7.5, '1/4' , '1/4' , .4375)]

do_all_screenshots = False

class Driver_Test(unittest.TestCase):
    '''
    Tests Driver
    '''
    def setUp(self):
        self.d = Driver()
        self.d.show()
        self.d.raise_()
        self.debug = self.d.config.debug
        QTest.qWaitForWindowExposed(self.d)
        if not utils.isMac():
            self.d.working_dir = 'Z:\Windows\pyRouterJig\images'
    def test_options(self):
        self.assertFalse(self.debug)
    def test_defaults(self):
        self.assertEqual(str(self.d.le_board_width.text()), '7 1/2')
        self.assertEqual(str(self.d.le_bit_width.text()), '1/2')
        self.assertEqual(str(self.d.le_bit_depth.text()), '3/4')
        self.assertEqual(str(self.d.le_bit_angle.text()), '0')
    def screenshot(self, do_screenshot=True):
        QTest.qWaitForWindowExposed(self.d)
        QTest.qWait(100)
        self.d._on_save(do_screenshot)
    def test_screenshots(self):
        # default
        print('************ default')
        self.d._on_fullscreen()
        self.screenshot()
        # default with caul
        print('************ caul')
        self.d.caul_action.setChecked(True)
        self.d._on_caul()
        self.screenshot()
        self.d.caul_action.setChecked(False)
        self.d._on_caul()
        # dovetail
        print('************ dovetail')
        self.d.le_bit_angle.clear()
        QTest.keyClicks(self.d.le_bit_angle, '7')
        self.d._on_bit_angle()
        self.assertEqual(str(self.d.le_bit_angle.text()), '7')
        self.screenshot()
        # fit
        print('************ fit')
        for w in [0, 1]:
            i = self.d.cb_wood[w].findText('Solid Fill')
            self.assertTrue(i >= 0)
            self.d.cb_wood[w].setCurrentIndex(i)
            self.d._on_wood(w)
        self.d.pass_id_action.setChecked(False)
        self.d._on_pass_id()
        self.d.fit_action.setChecked(True)
        self.d._on_fit()
        self.screenshot()
        self.d.pass_id_action.setChecked(True)
        self.d._on_pass_id()
        self.d.fit_action.setChecked(False)
        self.d._on_fit()
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
            i = self.d.cb_wood[w].findText('Solid Fill')
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
    def test_dovetails_fit(self):
        self.d._on_fullscreen()
        for w in [0, 1]:
            i = self.d.cb_wood[w].findText('Solid Fill')
            self.assertTrue(i >= 0)
            self.d.cb_wood[w].setCurrentIndex(i)
            self.d._on_wood(w)
        self.d.pass_id_action.setChecked(False)
        self.d._on_pass_id()
        self.d.finger_size_action.setChecked(False)
        self.d._on_finger_sizes()
        self.d.fit_action.setChecked(True)
        self.d._on_fit()
        self.d.le_bit_angle.clear()
        QTest.keyClicks(self.d.le_bit_angle, '9')
        self.d._on_bit_angle()
        self.assertEqual(str(self.d.le_bit_angle.text()), '9')
        self.d.le_board_width.clear()
        QTest.keyClicks(self.d.le_board_width, '4 1/4')
        self.d._on_board_width()
        self.assertEqual(str(self.d.le_board_width.text()), '4 1/4')
        self.d.le_bit_width.clear()
        QTest.keyClicks(self.d.le_bit_width, '3/8')
        self.d._on_bit_width()
        self.assertEqual(str(self.d.le_bit_width.text()), '3/8')
        self.d.le_bit_depth.clear()
        QTest.keyClicks(self.d.le_bit_depth, '1/4')
        self.d._on_bit_depth()
        self.assertEqual(str(self.d.le_bit_depth.text()), '1/4')
        self.screenshot()
        self.d.le_bit_depth.clear()
        QTest.keyClicks(self.d.le_bit_depth, '3/16')
        self.d._on_bit_depth()
        self.assertEqual(str(self.d.le_bit_depth.text()), '3/16')
        self.screenshot()
        self.d.le_bit_depth.clear()
        QTest.keyClicks(self.d.le_bit_depth, '0.197')
        self.d._on_bit_depth()
        self.assertEqual(str(self.d.le_bit_depth.text()), '0.197')
        self.screenshot()
    def test_incra_dovetail_cases(self):
        # Run the Incra guide test cases
        self.d.pass_id_action.setChecked(False)
        self.d._on_pass_id()
        self.d.pass_location_action.setChecked(True)
        self.d._on_pass_location()
        for c in cases:
            clears = [self.d.le_bit_width,
                      self.d.le_bit_depth,
                      self.d.le_bit_angle,
                      self.d.le_board_width]
            for cl in clears:
                cl.clear()
            QTest.keyClicks(self.d.le_bit_width, '{}'.format(c.width))
            self.d._on_bit_width()
            QTest.keyClicks(self.d.le_bit_depth, '{}'.format(c.depth))
            self.d._on_bit_depth()
            QTest.keyClicks(self.d.le_bit_angle, '{}'.format(c.angle))
            self.d._on_bit_angle()
            QTest.keyClicks(self.d.le_board_width, '{}'.format(c.board_width))
            self.d._on_board_width()
            cuts = self.d.boards[0].bottom_cuts
            bcuts = self.d.boards[1].top_cuts
            spacing = (cuts[2].passes[0] - cuts[1].passes[0]) / 32.
            print('incra', c.angle, spacing, c.spacing, spacing - c.spacing)
            self.assertTrue(abs(spacing - c.spacing) < 1.0e-5)
            if do_all_screenshots:
                self.screenshot()
    def test_variable_spaced(self):
        self.d.pass_id_action.setChecked(False)
        self.d._on_pass_id()
        self.d.pass_location_action.setChecked(False)
        self.d._on_pass_location()
        self.d.tabs_spacing.setCurrentIndex(self.d.var_spacing_id)
        for c in cases:
            print('doing variable', c.angle, c.width, c.depth)
            clears = [self.d.le_bit_width,
                      self.d.le_bit_depth,
                      self.d.le_bit_angle,
                      self.d.le_board_width]
            for cl in clears:
                cl.clear()
            QTest.keyClicks(self.d.le_bit_width, '{}'.format(c.width))
            self.d._on_bit_width()
            QTest.keyClicks(self.d.le_bit_depth, '{}'.format(c.depth))
            self.d._on_bit_depth()
            QTest.keyClicks(self.d.le_bit_angle, '{}'.format(c.angle))
            self.d._on_bit_angle()
            QTest.keyClicks(self.d.le_board_width, '{}'.format(c.board_width))
            self.d._on_board_width()
            n = self.d.cb_vsfingers.count()
            for i in range(n):
                self.d.cb_vsfingers.setCurrentIndex(i)
                self.d._on_cb_vsfingers(i)
                cuts = self.d.boards[0].bottom_cuts
                bcuts = self.d.boards[1].top_cuts
                spacing = (cuts[2].passes[0] - cuts[1].passes[0]) / 32.
                print(spacing)
                if do_all_screenshots:
                    self.screenshot()

if __name__ == '__main__':
    unittest.main()

