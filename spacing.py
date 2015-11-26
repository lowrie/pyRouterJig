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

'''
Contains the classes that define the finger width and spacing.
'''
from __future__ import print_function
from __future__ import division
from future.utils import lrange

import math
from operator import attrgetter
import router
from utils import my_round
from options import OPTIONS

class Spacing_Exception(Exception):
    '''
    Exception handler for spacings
    '''
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return self.msg

class Spacing_Param(object):
    '''
    Stores a generic parameter for the spacing algorithms.  Attributes:

    vMin: minimum value
    vMax: maximum value
    vInit: initial and current value
    '''
    def __init__(self, vMin, vMax, vInit):
        self.vMin = vMin
        self.vMax = vMax
        self.vInit = vInit

class Base_Spacing(object):
    '''
    Base class for spacing algorithms.

    Attributes:

    description: string description of algorithm
    bit: A Router_Bit object.
    board: A Board object.
    cuts: A list of Cut objects, which represent the female fingers in Board-A.
    active_fingers: Finger indices to highlight.  Index is with respect to 
                   female fingers in Board-A.
    labels: list of labels for the Spacing_Params

    cuts and full_labels are not set until set_cuts is called.
    '''
    labels = []
    def __init__(self, bit, board):
        self.description = 'NONE'
        self.bit = bit
        self.board = board
        self.active_fingers = []
        self.cuts = []
        self.full_labels = []
    def get_params(self):
        '''Returns a list of Spacing_Params that control the algoritm.'''
        pass

class Equally_Spaced(Base_Spacing):
    '''
    Computes cuts that are equally spaced, using (by default) the bit width,
    with the first cut centered on the board's edge.

    Parameters that control the spacing are:

    b_spacing: Extra spacing, beyond the bit width  added between the fingers
               of the B-board.  Default is 0.  The reported b_spacing has the
               bit width added on to this value.

    width: Width of fingers.  Default is the bit width.

    centered: If true, then a finger is centered on the board width.  If Always
    true for dovetail bits.  Default is true.
    '''
    labels = ['B-spacing', 'Width', 'Centered']
    def __init__(self, bit, board):
        Base_Spacing.__init__(self, bit, board)
    def get_params(self):
        p1 = Spacing_Param(0, self.board.width // 4, 0)
        p2 = Spacing_Param(self.bit.width, self.board.width // 2, self.bit.width)
        p3 = Spacing_Param(None, None, True)
        return [p1, p2, p3]
    def set_cuts(self, values=None):
        if values is not None:
            b_spacing = values[0]
            width = values[1]
            centered = values[2]
        else:
            b_spacing = 0
            width = self.bit.width
            centered = True
        units = self.bit.units
        label = units.intervals_to_string(2 * width + b_spacing, True)
        self.full_labels = ['B-spacing: ' + label,\
                            'Width: ' + units.intervals_to_string(width, True),\
                            'Centered']
        self.description = 'Equally spaced (' + self.full_labels[0] + \
                           ', ' + self.full_labels[1] + ')'
        self.cuts = [] # return value
        neck_width = my_round(self.bit.neck + width - self.bit.width + b_spacing)
        if neck_width < 1:
            raise Spacing_Exception('Specified bit paramters give a zero'
                                    ' or negative cut width (%d intervals) at'
                                    ' the surface!  Please change the'
                                    ' bit parameters width, depth, or angle.' % neck_width)
        # put a cut at the center of the board
        xMid = self.board.width // 2
        if centered or \
           self.bit.angle > 0: # always symm. for dovetail
            left = max(0, xMid - width // 2)
        else:
            left = max(0, (xMid // width) * width)
        right = min(self.board.width, left + width)
        self.cuts.append(router.Cut(left, right))
        # do left side of board
        i = left - neck_width
        while i > 0:
            li = max(i - width, 0)
            if i - li > OPTIONS['min_finger_width']:
                self.cuts.append(router.Cut(li, i))
            i = li - neck_width
        # do right side of self.board
        i = right + neck_width
        while i < self.board.width:
            ri = min(i + width, self.board.width)
            if ri - i > OPTIONS['min_finger_width']:
                self.cuts.append(router.Cut(i, ri))
            i = ri + neck_width
        # If we have only one cut the entire width of the board, then
        # the board width is too small for the bit
        if self.cuts[0].xmin == 0 and self.cuts[0].xmax == self.board.width:
            raise Spacing_Exception('Unable to compute a equally-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('xmin'))

class Variable_Spaced(Base_Spacing):
    '''
    Computes variable-spaced cuts, where the center cut (always centered on
    board) is the widest, with each cut decreasing linearly as you move to the edge.

    Parameters that control the spacing are:

    Fingers: Roughly the number of full fingers on either the A or B board.
    '''
    labels = ['Fingers']
    def __init__(self, bit, board):
        Base_Spacing.__init__(self, bit, board)
        # eff_width is the effective width, an average of the bit width
        # and the neck width
        self.eff_width = my_round(0.5 * (self.bit.width + self.bit.neck))
        self.wb = self.board.width // self.eff_width
        self.alpha = (self.wb + 1) % 2
        # min and max number of fingers
        self.mMin = max(3 - self.alpha, my_round(math.ceil(math.sqrt(self.wb))))
        self.mMax = my_round((self.wb - 1.0 + self.alpha) // 2)
        if self.mMax < self.mMin:
            raise Spacing_Exception('Unable to compute a variable-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        self.mDefault = (self.mMin + self.mMax) // 2
    def get_params(self):
        p1 = Spacing_Param(self.mMin, self.mMax, self.mDefault)
        return [p1]
    def set_cuts(self, values=None):
        # set the number of fingers, m
        if values is not None:
            m = values[0]
        else:
            m = self.mDefault
        units = self.bit.units
        self.full_labels = ['Fingers: %d' % m]
        self.description = 'Variable Spaced (' + self.full_labels[0] + ')'
        # c is the ideal center-cut width
        c = self.eff_width * ((m - 1.0) * self.wb - m * (m + 1.0) + self.alpha * m) /\
            (m * m - 2.0 * m - 1.0 + self.alpha)
        # d is the ideal decrease in finger width for each finger away from center finger
        d = (c - self.eff_width) / (m - 1.0)
        # compute fingers on one side of the center and the center and store them
        # in intervals.  Keep a running total of sizes.
        intervals = [0] * (m + 1)
        ivals = 0
        for i in lrange(1, m+1):
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
        if OPTIONS['debug']:
            print('intervals', intervals)
        # Adjustments for dovetails
        deltaP = self.bit.width - self.eff_width
        deltaM = my_round(self.eff_width - self.bit.neck)
        # put a cut at the center of the board
        xMid = self.board.width // 2
        width = intervals[0] + deltaP
        left = max(0, xMid -  width // 2)
        right = min(self.board.width, left + width)
        self.cuts = [router.Cut(left, right)]
        # do the remaining cuts
        do_cut = False
        for i in lrange(1, m+1):
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
        self.cuts = sorted(self.cuts, key=attrgetter('xmin'))

class Edit_Spaced(Base_Spacing):
    '''
    Allows for user to interactively edit the cuts.
    '''
    labels = []
    def __init__(self, bit, board):
        Base_Spacing.__init__(self, bit, board)
    def get_params(self):
        return []
    def set_cuts(self, cuts):
        '''
        Sets cuts to the input cuts
        '''
        self.cuts = cuts
        self.full_labels = []
        self.description = 'Edit spacing'
        self.active_fingers = [0]
    def get_limits(self, f):
        '''
        Returns the x-coordinate limits of the finger index f
        '''
        xmin = 0
        xmax = self.board.width
        neck_width = my_round(self.bit.neck)
        if f > 0:
            xmin = self.cuts[f - 1].xmax + neck_width
        if f < len(self.cuts) - 1:
            xmax = self.cuts[f + 1].xmin - neck_width
        return (xmin, xmax)
    def finger_shift_left(self):
        '''
        Shifts the active fingers 1 interval to the left
        '''
        msg = 'Shifted active fingers 1 interval to left'
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            w = max(c.xmax - c.xmin, self.bit.width)
            xmin = max(xmin, c.xmin - 1)
            if xmin == c.xmin:
                msg = 'Unable to shift a finger to left'
            c.xmin = xmin
            c.xmax = min(c.xmin + w, self.board.width)
            self.cuts[f] = c
        return msg
    def finger_shift_right(self):
        '''
        Shifts the active fingers 1 interval to the right
        '''
        msg = 'Shifted active fingers 1 interval to right'
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            w = max(c.xmax - c.xmin, self.bit.width)
            xmax = min(xmax, c.xmax + 1)
            if xmax == c.xmax:
                msg = 'Unable to shift a finger to right'
            c.xmax = xmax
            c.xmin = max(c.xmax - w, 0)
            self.cuts[f] = c
        return msg
    def finger_widen_left(self):
        '''
        Increases the active fingers width on the left side by 1 interval
        '''
        msg = 'Widened finger 1 interval on left'
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmin > xmin:
                c.xmin -= 1
                self.cuts[f] = c
            else:
                msg = 'Unable to widen a finger on left any further'
        return msg
    def finger_widen_right(self):
        '''
        Increases the active fingers width on the right side by 1 interval
        '''
        msg = 'Widened finger 1 interval on right'
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmax < xmax:
                c.xmax += 1
                self.cuts[f] = c
            else:
                msg = 'Unable to widen a finger on right any further'
        return msg
    def finger_trim_left(self):
        '''
        Decreases the active fingers width on the left side by 1 interval
        '''
        msg = 'Trimmed finger on left 1 interval'
        for f in self.active_fingers:
            c = self.cuts[f]
            wmin = self.bit.width
            if c.xmax == self.board.width:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                msg = 'Unable to trim a finger on left any further'
            else:
                c.xmin += 1
                self.cuts[f] = c
        return msg
    def finger_trim_right(self):
        '''
        Decreases the active fingers width on the right side by 1 interval
        '''
        msg = 'Trimmed finger on right 1 interval'
        for f in self.active_fingers:
            c = self.cuts[f]
            wmin = self.bit.width
            if c.xmin == 0:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                return 'Unable to trim a finger on right any further'
            else:
                c.xmax -= 1
                self.cuts[f] = c
        return msg
    def finger_increment_active(self, inc):
        '''
        Sets the active finger to the finger to the right, unless already
        at the last finger, in which case the active finger is cycled back
        to the first finger on the left.
        '''
        for k in lrange(len(self.active_fingers)):
            self.active_fingers[k] = (self.active_fingers[k] + inc) % len(self.cuts)
        return 'Switched active fingers'
    def finger_delete_active(self):
        '''
        Deletes the active fingers.
        '''
        msg = 'Deleted active fingers'
        for f in self.active_fingers:
            if len(self.cuts) < 2:
                msg = 'Unable to delete last finger'
                break
            c = self.cuts[0:f]
            c.extend(self.cuts[f + 1:])
            self.cuts = c
        self.active_fingers = [0]
        return msg
    def finger_add(self):
        '''
        Adds a finger to the first location possible, searching from the left.
        The active finger is set the the new finger.
        '''
        neck_width = my_round(self.bit.neck)
        index = None
        if self.cuts[0].xmin > self.bit.neck:
            if OPTIONS['debug']:
                print('add at left')
            index = 0
            xmin = 0
            xmax = self.cuts[0].xmin - neck_width
        wadd = 2 * self.bit.width + neck_width
        wdelta = self.bit.width - neck_width
        for i in lrange(1, len(self.cuts)):
            if self.cuts[i].xmin - self.cuts[i - 1].xmax + wdelta >= wadd:
                if OPTIONS['debug']:
                    print('add in finger')
                index = i
                xmin = self.cuts[i - 1].xmax + neck_width
                xmax = xmin + self.bit.width
                break
            elif self.cuts[i].xmax - self.cuts[i].xmin >= wadd:
                if OPTIONS['debug']:
                    print('add in cut')
                index = i + 1
                xmin = self.cuts[i].xmax - self.bit.width
                xmax = self.cuts[i].xmax
                self.cuts[i].xmax = self.cuts[i].xmin + self.bit.width
                break
        if index is None and \
           self.cuts[-1].xmax < self.board.width - self.bit.neck:
            if OPTIONS['debug']:
                print('add at right')
            index = len(self.cuts)
            xmax = self.board.width
            xmin = self.cuts[-1].xmax + neck_width
        if index is None:
            return 'Unable to add finger'
        c = self.cuts[0:index]
        c.append(router.Cut(xmin, xmax))
        c.extend(self.cuts[index:])
        self.cuts = c
        self.active_fingers = [index]
        return 'Added finger'
