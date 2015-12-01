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
import copy
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
    cursor_finger: Finger index to highlight perimeter.  Index is with respect to 
                   female fingers in Board-A.
    active_fingers: Finger indices to highlight with fill.  Index is with respect to 
                    female fingers in Board-A.
    labels: list of labels for the Spacing_Params

    cuts and full_labels are not set until set_cuts is called.
    '''
    labels = []

    def __init__(self, bit, board):
        self.description = 'NONE'
        self.bit = bit
        self.board = board
        self.cursor_finger = None
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
        label = units.increments_to_string(2 * width + b_spacing, True)
        self.full_labels = ['B-spacing: ' + label,\
                            'Width: ' + units.increments_to_string(width, True),\
                            'Centered']
        self.description = 'Equally spaced (' + self.full_labels[0] + \
                           ', ' + self.full_labels[1] + ')'
        self.cuts = [] # return value
        neck_width = my_round(self.bit.neck + width - self.bit.width + b_spacing)
        if neck_width < 1:
            raise Spacing_Exception('Specified bit paramters give a zero'
                                    ' or negative cut width (%d increments) at'
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
        # in increments.  Keep a running total of sizes.
        increments = [0] * (m + 1)
        ivals = 0
        for i in lrange(1, m+1):
            increments[i] = int(c - d * i)
            ivals += 2 * increments[i]
        # Set the center increment.  This takes up the slop in the rounding and increment
        # resolution.
        increments[0] = self.board.width - ivals
        if increments[0] < increments[1]:
            # The center increment is narrower than the adjacent increment,
            # so reset it to the adjacent increment and get rid of a finger.
            increments[0] = increments[1]
            m -= 1
        if OPTIONS['debug']:
            print('increments', increments)
        # Adjustments for dovetails
        deltaP = self.bit.width - self.eff_width
        deltaM = my_round(self.eff_width - self.bit.neck)
        # put a cut at the center of the board
        xMid = self.board.width // 2
        width = increments[0] + deltaP
        left = max(0, xMid -  width // 2)
        right = min(self.board.width, left + width)
        self.cuts = [router.Cut(left, right)]
        # do the remaining cuts
        do_cut = False
        for i in lrange(1, m+1):
            if do_cut:
                width = increments[i] + deltaP
                farLeft = max(0, left - width)
                self.cuts.append(router.Cut(farLeft, left))
                farRight = min(self.board.width, right + width)
                self.cuts.append(router.Cut(right, farRight))
            else:
                width = increments[i] - deltaM
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
        self.undo_cuts = [] # list of cuts to undo

    def get_params(self):
        return []

    def set_cuts(self, cuts):
        '''
        Sets cuts to the input cuts
        '''
        self.cuts = cuts
        self.full_labels = []
        self.description = 'Edit spacing'
        self.cursor_finger = 0
        self.active_fingers = [self.cursor_finger]
        self.undo_cuts = []

    def changes_made(self):
        '''
        Returns true if editing changes have been made
        '''
        return len(self.undo_cuts) > 0

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

    def undo(self):
        '''
        Undoes the last change to cuts
        '''
        if len(self.undo_cuts) > 0:
            self.cuts = self.undo_cuts.pop()

    def finger_move_left(self):
        '''
        Moves the active fingers 1 increment to the left
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        delete_finger = False
        s = sorted(self.active_fingers)
        for f in s:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            xmin = max(xmin, c.xmin - 1)
            w = c.xmax - c.xmin
            if c.xmin == 0:
                w -= 1
            else:
                w = max(w, self.bit.width)
            if w == 0:
                # note its possible for only one finger to be deleted
                delete_finger = True
            else:
                if xmin == c.xmin and xmin > 0:
                    noop.append(f)
                    msg = 'Unable to move finger to left'
                else:
                    c.xmin = xmin
                    c.xmax = min(c.xmin + w, self.board.width)
                    self.cuts[f] = c
                    op.append(f)
        if len(op) > 0 or delete_finger:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg = 'Moved finger indices ' + `op` + ' to left 1 increment'
        else:
            msg = 'Moved no fingers'
        if len(noop) > 0:
            msg += '; unable to move indices ' + `noop`
        if delete_finger:
            msg += '; deleted finger 0'
            self.finger_delete(0)
        return msg

    def finger_move_right(self):
        '''
        Moves the active fingers 1 increment to the right
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        delete_finger = False
        s = sorted(self.active_fingers, reverse=True)
        for f in s:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            xmax = min(xmax, c.xmax + 1)
            w = c.xmax - c.xmin
            if c.xmax == self.board.width:
                w -= 1
            else:
                w = max(w, self.bit.width)
            if w == 0:
                # note its possible for only one finger to be deleted
                delete_finger = True
            else:
                if xmax == c.xmax and xmax < self.board.width:
                    noop.append(f)
                else:
                    c.xmax = xmax
                    c.xmin = max(c.xmax - w, 0)
                    self.cuts[f] = c
                    op.append(f)
        if len(op) > 0 or delete_finger:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg = 'Moved finger indices ' + `op` + ' to right 1 increment'
        else:
            msg = 'Moved no fingers'
        if len(noop) > 0:
            msg += '; unable to move indices ' + `noop`
        if delete_finger:
            f = len(self.cuts) - 1
            msg += '; deleted finger %d' % f
            self.finger_delete(f)
            self.active_fingers = [len(self.cuts) - 1]
        return msg

    def finger_widen_left(self):
        '''
        Increases the active fingers width on the left side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmin > xmin:
                c.xmin -= 1
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(F)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = 'Widened finger indices ' + `op` + ' on left 1 increment'
        else:
            msg = 'Widened no fingers'
        if len(noop) > 0:
            msg += '; unable to widen indices ' + `noop`
        return msg

    def finger_widen_right(self):
        '''
        Increases the active fingers width on the right side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_fingers:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmax < xmax:
                c.xmax += 1
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(f)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = 'Widened finger indices ' + `op` + ' on right 1 increment'
        else:
            msg = 'Widened no fingers'
        if len(noop) > 0:
            msg += '; unable to widen indices ' + `noop`
        return msg

    def finger_trim_left(self):
        '''
        Decreases the active fingers width on the left side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_fingers:
            c = self.cuts[f]
            wmin = self.bit.width
            if c.xmax == self.board.width:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                noop.append(f)
            else:
                c.xmin += 1
                self.cuts[f] = c
                op.append(f)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = 'Trimmed finger indices ' + `op` + ' on left 1 increment'
        else:
            msg = 'Trimmed no fingers'
        if len(noop) > 0:
            msg += '; unable to trim indices ' + `noop`
        return msg

    def finger_trim_right(self):
        '''
        Decreases the active fingers width on the right side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_fingers:
            c = self.cuts[f]
            wmin = self.bit.width
            if c.xmin == 0:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                noop.append(f)
            else:
                c.xmax -= 1
                self.cuts[f] = c
                op.append(f)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = 'Trimmed finger indices ' + `op` + ' on right 1 increment'
        else:
            msg = 'Trimmed no fingers'
        if len(noop) > 0:
            msg += '; unable to trim indices ' + `noop`
        return msg

    def finger_increment_cursor(self, inc):
        '''
        Increments the cursor finger, cyclicly.  Increment can be positive or negative.
        '''
        self.cursor_finger = (self.cursor_finger + inc) % len(self.cuts)
        return 'Moved finger cursor to finger index %d' % self.cursor_finger

    def finger_toggle(self):
        '''
        Toggles Increments the cursor finger, cyclicly.  Increment can be positive or negative.
        '''
        if self.cursor_finger in self.active_fingers:
            self.active_fingers.remove(self.cursor_finger)
            msg = 'Deactivated finger index %d' % self.cursor_finger
        else:
            self.active_fingers.append(self.cursor_finger)
            msg = 'Activated finger index %d' % self.cursor_finger
        return msg

    def finger_all_active(self):
        '''
        Sets all fingers as active.
        '''
        self.active_fingers = lrange(len(self.cuts))
        return 'All fingers activated'

    def finger_all_not_active(self):
        '''
        Deactivate all fingers.
        '''
        self.active_fingers = []
        return 'All fingers deactivated'

    def finger_delete(self, f):
        '''
        Deletes finger of index f.  Returns True if able to delete the finger,
        False otherwise.
        '''
        if len(self.cuts) < 2:
            return False
        c = self.cuts[0:f]
        c.extend(self.cuts[f + 1:])
        self.cuts = c
        return True

    def finger_delete_active(self):
        '''
        Deletes the active fingers.
        '''
        cuts_save = copy.deepcopy(self.cuts)
        deleted = []
        failed = False
        # delete in reverse order, so that modifications to cuts don't affect index values
        rev = sorted(self.active_fingers, reverse=True)
        for f in rev:
            if not self.finger_delete(f):
                failed = True
                break
            deleted.append(f)
        self.cursor_finger = 0
        self.active_fingers = [self.cursor_finger]
        if len(deleted) > 0:
            msg = 'Deleted finger indices ' + `deleted`
            self.undo_cuts.append(cuts_save)
        else:
            msg = 'Deleted no fingers'
        if failed:
            msg += '; unable to delete last finger'
        return msg

    def finger_add(self):
        '''
        Adds a finger to the first location possible, searching from the left.
        The active finger is set the the new finger.
        '''
        neck_width = my_round(self.bit.neck)
        index = None
        cuts_save = copy.deepcopy(self.cuts)
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
        self.undo_cuts.append(cuts_save)
        c = self.cuts[0:index]
        c.append(router.Cut(xmin, xmax))
        c.extend(self.cuts[index:])
        self.cuts = c
        self.cursor_finger = index
        self.active_fingers = [index]
        return 'Added finger'
