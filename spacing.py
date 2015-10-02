###########################################################################
#
# Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)
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
Contains the classes that define the finger width and spacing.
'''

import math
from operator import attrgetter
import utils
from utils import options, my_round
import router

class Spacing_Exception(Exception):
    '''
    Exception handler for spacings
    '''
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Spacing_Param:
    '''
    Stores a generic parameter for the spacing algorithms.  Attributes:

    label: a string describing the parameter
    vMin: minimum value
    vMax: maximum value
    vInit: initial and current value
    '''
    def __init__(self, label, vMin, vMax, vInit):
        self.label = label
        self.vMin  = vMin
        self.vMax  = vMax
        self.vInit = vInit

class Base_Spacing:
    '''
    Base class for spacing algorithms.

    Attributes:

    description: string description of algorithm
    bit: A Router_Bit object.
    board: A Board object.
    cuts: A list of Cut objects, which represent the female fingers in Board-A.
    '''
    def __init__(self, bit, board):
        self.description = 'NONE'
        self.bit         = bit
        self.board       = board
    def get_params(self):
        '''Returns a list of Spacing_Params the control the algoritm.'''
        return ()
    def set_cuts(self):
        '''Computes the attribute "cuts".'''
        self.cuts = []

class Equally_Spaced(Base_Spacing):
    '''
    Computes cuts that are equally spaced, using (by default) the bit width,
    with the first cut centered on the board's edge.

    Parameters that control the spacing are:

    b_spacing: Extra spacing, beyond the bit width  added between the fingers 
               of the B-board.  Default is 0.
    
    width: Width of fingers.  Default is the bit width.

    centered: If true, then a finger is centered on the board width.  If Always
    true for dovetail bits.  Default is true.
    '''
    def __init__(self, bit, board):
        Base_Spacing.__init__(self, bit, board)
    def get_params(self):
        p1 = Spacing_Param('B-spacing', 0, self.board.width / 4, 0)
        p2 = Spacing_Param('Width', self.bit.width, self.board.width / 2, self.bit.width)
        p3 = Spacing_Param('Centered', None, None, True)
        return [p1, p2, p3]
    def set_cuts(self, b_spacing=0, width=None, centered=True, values=None):
        if values is not None:
            b_spacing = values[0]
            width = values[1]
            centered = values[2]
        elif width is None:
            width = self.bit.width
        self.description = 'Equally spaced (B-spacing=' +\
                           utils.intervals_to_string(b_spacing, True) +\
                           ', width=' +\
                            utils.intervals_to_string(width, True) +\
                            ')'
        self.cuts = [] # return value
        neck_width = my_round(self.bit.neck + width - self.bit.width + b_spacing)
        if neck_width < 1:
            raise Spacing_Exception('Specified bit paramters give a zero'
                                    ' or negative cut width (%d intervals) at the surface!  Please change the'
                                    ' bit parameters width, depth, or angle.' % neck_width)
        # put a cut at the center of the board
        xMid = self.board.width / 2
        if centered or \
           self.bit.angle > 0: # always symm. for dovetail
            left = max(0, xMid - width / 2)
        else:
            left = max(0, (xMid / width) * width)
        right = min(self.board.width, left + width)
        self.cuts.append(router.Cut(left, right))
        # do left side of board
        i = left - neck_width
        while i > 0:
            li = max(i - width, 0)
            if i - li > options.min_finger_width:
                self.cuts.append(router.Cut(li, i))
            i = li - neck_width
        # do right side of self.board
        i = right + neck_width
        while i < self.board.width:
            ri = min(i + width, self.board.width)
            if ri - i > options.min_finger_width:
                self.cuts.append(router.Cut(i, ri))
            i = ri + neck_width
        # If we have only one cut the entire width of the board, then
        # the board width is too small for the bit
        if self.cuts[0].L == 0 and self.cuts[0].R == self.board.width:
            raise Spacing_Exception('Unable to compute a equally-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('L'))

class Variable_Spaced(Base_Spacing):
    '''
    Computes variable-spaced cuts, where the center cut (always centered on
    board) is the widest, with each cut decreasing linearly as you move to the edge.

    Parameters that control the spacing are:

    Fingers: Roughly the number of full fingers on either the A or B board.
    '''
    def __init__(self, bit, board):
        Base_Spacing.__init__(self, bit, board)
        # eff_width is the effective width, an average of the bit width
        # and the neck width
        self.eff_width = my_round(0.5 * (self.bit.width + self.bit.neck))
        self.wb = self.board.width / self.eff_width
        self.alpha = (self.wb + 1) % 2
        # min and max number of fingers
        self.mMin = max(3 - self.alpha, my_round(math.ceil(math.sqrt(self.wb))))
        self.mMax = my_round(math.floor((self.wb - 1.0 + self.alpha) / 2))
        if self.mMax < self.mMin:
            raise Spacing_Exception('Unable to compute a variable-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        self.mDefault = (self.mMin + self.mMax) / 2
    def get_params(self):
        p1 = Spacing_Param('Fingers', self.mMin, self.mMax, self.mDefault)
        return [p1]
    def set_cuts(self, m=None, values=None):
        # set the number of fingers, m
        if values is not None:
            m = values[0]
        elif m is None:
            m = self.mDefault
        self.description = 'Variable Spaced (Fingers=%d)' % (m)
        # c is the ideal center-cut width
        c = self.eff_width * ((m - 1.0) * self.wb - m * (m + 1.0) + self.alpha * m) /\
            (m * m - 2.0 * m - 1.0 + self.alpha)
        # d is the ideal decrease in finger width for each finger away from center finger
        d = (c - self.eff_width) / (m - 1.0)
        # compute fingers on one side of the center and the center and store them
        # in intervals.  Keep a running total of sizes.
        intervals = [0] * (m + 1)
        ivals = 0
        for i in range(1, m+1):
            intervals[i] = int(c - d * i)
            ivals += 2 * intervals[i]
        # Set the center interval.  This takes up the slop in the rounding and interval
        # resolution.
        intervals[0] = self.board.width - ivals
        if intervals[0] < intervals[1]:
            # The center interval is narrower than the adjacent interval,
            # so reset it to the adjacent interval and get rid of a finger.
            intervals[0] = intervals[1]
            m -= 1
        if options.debug:
            print 'intervals', intervals
        # Adjustments for dovetails
        deltaP = self.bit.width - self.eff_width
        deltaM = my_round(self.eff_width - self.bit.neck)
        # put a cut at the center of the board
        xMid = self.board.width / 2
        width = intervals[0] + deltaP
        left = max(0, xMid -  width / 2)
        right = min(self.board.width, left + width)
        self.cuts = [router.Cut(left, right)]
        # do the remaining cuts
        do_cut = False
        for i in range(1, m+1):
            if do_cut:
                width = intervals[i] + deltaP
                farLeft = max(0, left - width)
                self.cuts.append(router.Cut(farLeft, left))
                farRight = min(self.board.width, right + width)
                self.cuts.append(router.Cut(right, farRight))
            else:
                width = intervals[i] - deltaM
                farLeft = max(0, left - width)
                farRight = min(self.board.width, right + width)
            left = farLeft
            right = farRight
            do_cut = (not do_cut)
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('L'))
