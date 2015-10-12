###########################################################################
#
# Copyright 2015 Robert B. Lowrie (http://github.com/lowrie)
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

import spacing
import utils
from options import Options

class Doc:
    '''
    Defines documentation strings.
    '''
    short_desc = 'pyRouterJig is a joint layout tool for woodworking.'

    license = '<p>\
    Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)\
    <p>\
    pyRouterJig is free software: you can redistribute it and/or modify it under\
    the terms of the GNU General Public License as published by the Free Software\
    Foundation, either version 3 of the License, or (at your option) any later\
    version.\
    <p>\
    pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY\
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR\
    A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\
    You should have received a copy of the GNU General Public License along with\
    pyRouterJig; see the file LICENSE. If not, see \
    <a href=http://www.gnu.org/licenses/>http://www.gnu.org/licenses/</a>.\
    <p>\
    <h3>USE AT YOUR OWN RISK!</h3>'
    
    board_width = '<b>Board Width</b> is the board width (in%s) of \
    the joint.'

    bit_width = '<b>Bit Width</b> is the maximum cutting width (in%s) of \
    the router bit.'

    bit_depth = '<b>Bit Depth</b> is the cutting depth (in%s) of the \
    router bit.'

    bit_angle = '<b>Bit Angle</b> is the angle (in degrees) of the router \
    bit for dovetail bits.  Set to zero for straight bits.'

    es_slider0 = '<b>%s</b> slider allows you to specify additional \
    spacing between the Board-B fingers'

    es_slider1 = '<b>%s</b> slider allows you to specify additional \
    width added to both Board-A and Board-B fingers.'

    es_centered = 'Check <b>%s</b> to force a finger to be centered on \
    the board.'

    vs_slider0 = '<b>%s</b> slider allows you to specify the number of \
    fingers. At its minimum value, the width of the center finger is \
    maximized. At its maximum value, the width of the center finger is \
    minimized, and the result is the roughly the same as equally-spaced \
    with, zero "B-spacing", zero "Width", and the "Centered" option \
    checked.'

    statics_set = False
    @staticmethod
    def set_statics():
        if Doc.statics_set: return
        sunits = Options.units.units_string(verbose=True)
        Doc.board_width = Doc.board_width % sunits
        Doc.bit_width = Doc.bit_width % sunits
        Doc.bit_depth = Doc.bit_depth % sunits
        labels = spacing.Equally_Spaced.labels
        Doc.es_slider0 = Doc.es_slider0 % labels[0]
        Doc.es_slider1 = Doc.es_slider1 % labels[1]
        Doc.es_centered = Doc.es_centered % labels[2]
        Doc.vs_slider0 = Doc.vs_slider0 % spacing.Variable_Spaced.labels[0]
        Doc.statics_set = True
