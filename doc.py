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
Defines documentation helpers.
'''
import spacing


class Doc(object):
    '''
    Defines documentation strings.
    '''

    def __init__(self, units):
        self.sunits = units.units_string(verbose=True)
        self.transl = units.transl

        self._short_desc = self.transl.tr(
            '<i>pyRouterJig</i> is a joint layout tool for woodworking.')

        self._license = self.transl.tr('<p>\
            Copyright 2015-2018 Robert B. Lowrie (pyrouterjig@lowrielodge.org)\
            <p>\
            <i>pyRouterJig</i> is free software: you can redistribute it and/or modify it under\
            the terms of the GNU General Public License as published by the Free Software\
            Foundation, either version 3 of the License, or (at your option) any later\
            version.\
            <p>\
            <i>pyRouterJig</i> is distributed in the hope that it will be useful, but WITHOUT ANY\
            WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR\
            A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\
            You should have received a copy of the GNU General Public License along with\
            <i>pyRouterJig</i>; see the file LICENSE. If not, see \
            <a href=http://www.gnu.org/licenses/>http://www.gnu.org/licenses/</a>.\
            <p>\
            This software and its output is not an INCRA product.  The authors have no\
            connection with INCRA (or Taylor Design Group, Inc.), aside from being users\
            themselves of their products.\
            <p>\
            <h3>USE AT YOUR OWN RISK!</h3>')

        self._board_width = self.transl.tr('<b>Board Width</b> is the board width (in%s) of the joint.')

        self._bit_width = self.transl.tr('<b>Bit Width</b> is the maximum cutting width (in%s) of the router bit.')

        self._bit_depth = self.transl.tr('<b>Bit Depth</b> is the cutting depth (in%s) of the router bit.')

        self._bit_angle = self.transl.tr('<b>Bit Angle</b> is the angle (in degrees) of the router bit for dovetail bits. Set to zero for straight bits.')

        self._top_board = self.transl.tr(
            '<b>Top Board</b> is the wood image to use for the top board.')

        self._bottom_board = self.transl.tr(
            '<b>Bottom Board</b> is the wood image to use for the bottom board.')

        self._double_board = self.transl.tr(
            '<b>Double Board</b> is the wood image to use for the double board.'
            ' If NONE, there is no double board.')

        self._dd_board = self.transl.tr(
            '<b>Double-Double Board</b> is the wood image to use for the double-double board. If NONE, there is no double-double board.')

        self._double_thickness = self.transl.tr(
            '<b>Thickness</b> is the thickness (in%s) of the double board.')

        self._dd_thickness = self.transl.tr(
            '<b>Thickness</b> is the thickness (in%s) of the double-double board.')

        self._es_slider0 = self.transl.tr('<b>%s</b> slider allows you to specify additional spacing between the fingers')

        self._es_slider1 = self.transl.tr('<b>%s</b> slider allows you to specify additional width added to the fingers.')

        self._es_centered = self.transl.tr('Check <b>%s</b> to force a finger to be centered on the board.')

        self._cb_vsfingers = self.transl.tr('<b>%s</b> specifies the approximate number of<br>\
fingers. At its minimum value, the width of the center finger is<br>\
maximized. At its maximum value, the width of the center finger is<br>\
minimized, and the result is the roughly the same as equally-spaced<br>\
using zero "Spacing", zero "Width", and the "Centered" option checked.')

    def short_desc(self):
        return self._short_desc

    def license(self):
        return self._license

    def board_width(self):
        return self._board_width % self.sunits

    def bit_width(self):
        return self._bit_width % self.sunits

    def bit_depth(self):
        return self._bit_depth % self.sunits

    def bit_angle(self):
        return self._bit_angle

    def top_board(self):
        return self._top_board

    def bottom_board(self):
        return self._bottom_board

    def double_board(self):
        return self._double_board

    def dd_board(self):
        return self._dd_board

    def double_thickness(self):
        return self._double_thickness % self.sunits

    def dd_thickness(self):
        return self._dd_thickness % self.sunits

    def es_slider0(self):
        return self._es_slider0 % spacing.Equally_Spaced.keys[0]

    def es_slider1(self):
        return self._es_slider1 % spacing.Equally_Spaced.keys[1]

    def es_centered(self):
        return self._es_centered % spacing.Equally_Spaced.keys[2]

    def cb_vsfingers(self):
        return self._cb_vsfingers % spacing.Variable_Spaced.keys[0]
