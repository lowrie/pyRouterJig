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
Contains the classes that define the finger width and spacing.
'''
from __future__ import print_function
from __future__ import division
from future.utils import lrange

from decimal import *
import math
import copy
from operator import attrgetter
import router
import utils

def dump_cuts(cuts):
    '''Dumps the cuts to the screen...this is for debugging.'''
    print('Min\tMax\tCenter')
    for c in cuts:
        print( '{0:2f}\t{1:3f}\t{2:4f}'.format(c.xmin, c.xmax, c.midPass))

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
    Stores a parameters for the spacing algorithms.  Attributes:

    vMin: minimum value
    vMax: maximum value
    v: initial and current value

    These values are typically dictionaries
    '''
    def __init__(self, vMin, vMax, v):
        self.vMin = vMin
        self.vMax = vMax
        self.v = v

class Base_Spacing(object):
    '''
    Base class for spacing algorithms.

    Attributes:

    description: string description of algorithm
    bit: A Router_Bit object.
    boards: A list of Board objects.
    cuts: A list of Cut objects, which represent the female fingers in Board-A.
    cursor_cut: Cut index to highlight perimeter.  Index is with respect to
                   female cuts in Board-A.
    active_cuts: Cut indices to highlight with fill.  Index is with respect to
                    female cuts in Board-A.
    labels: list of labels for the Spacing_Params
    id: Unique integer identifier for each concrete class

    cuts and labels are not set until set_cuts is called.
    '''
    labels = []

    def __init__(self, bit, boards, config):
        getcontext().prec = 6
        self.description = 'NONE'
        self.bit = bit
        self.boards = boards
        self.config = config
        self.cursor_cut = None
        self.active_cuts = []
        self.cuts = []
        self.labels = []

        # compute the increase in effective bit width from the double* boards
        self.dhtot = 0
        if boards[2].active:
            self.dhtot += boards[2].dheight
            if boards[3].active:
                self.dhtot += boards[3].dheight

    def write(self, fd):
        '''Writes the class to a file'''

class Equally_Spaced(Base_Spacing):
    '''
    Computes cuts that are equally spaced, using (by default) the bit width,
    with the first cut centered on the board's edge.

    Parameters that control the spacing are:

    spacing: Extra spacing, beyond the bit width added between the cuts
             of the board.  Default is 0.

    width: Width of fingers.  Default is the bit width.

    centered: If true, then a finger is centered on the board width.  Always
    true for dovetail bits.  Default is true.
    '''
    keys = ['Spacing', 'Width', 'Centered']

    def __init__(self, bit, boards, config):
        Base_Spacing.__init__(self, bit, boards, config)

        dh2 = 2 * self.dhtot
        t = [Spacing_Param(0, self.boards[0].width // 4 + dh2, 0),\
             Spacing_Param(math.floor(self.bit.width) + dh2, self.boards[0].width // 2 + dh2, \
                           math.floor(self.bit.width) + dh2),\
             Spacing_Param(None, None, True)]
        self.params = {}
        for i in lrange(len(t)):
            self.params[self.keys[i]] = t[i]

    def set_cuts(self):
        '''
        Sets the cuts to make the joint
        '''
        spacing = self.params['Spacing'].v  - 2 *  self.dhtot
        width = Decimal( math.floor(self.params['Width'].v) ) + Decimal(self.bit.width_f - math.floor(self.bit.width_f) )
        centered = self.params['Centered'].v

        board_width = self.boards[0].width
        units = self.bit.units
        label = units.increments_to_string(spacing, True)

        self.labels = self.keys[:]
        self.labels[0] += ': ' + label
        self.labels[1] += ': ' + units.increments_to_string(width, True)
        self.description = 'Equally spaced (' + self.labels[0] + \
                           ', ' + self.labels[1] + ')'

        self.cuts = [] # return value
#        neck_width = width + spacing - 2 * utils.my_round(self.bit.offset)
#        neck_width = width + spacing - utils.my_round(self.bit.offset)
#        neck_width = utils.my_round(width + spacing - self.bit.offset)
        neck_width = (self.bit.midline + width - self.bit.width_f) * 2  + spacing
        offset = Decimal(round(self.bit.offset, 3))

        if neck_width < 1:
            raise Spacing_Exception('Specified bit paramters give a zero'
                                    ' or negative cut width (%d increments) at'
                                    ' the surface!  Please change the'
                                    ' bit parameters width, depth, or angle.' % neck_width)


        # we working thru the midline now
        if centered or \
           self.bit.angle > 0: # always symm. for dovetail
            # put a cut at the center of the board
            xMid = Decimal(board_width // 2)
            xMid += Decimal(math.floor(width) / 2 - math.floor(width) // 2)  # even round
            left = Decimal(  max(0, xMid - width / 2))
        else:
            xMid = board_width - width / 2

        left = Decimal(max(0, xMid - width / 2))
        #left = Decimal(board_width )

        right = Decimal( min(board_width, left + width) )
        self.cuts.append( router.Cut( left, right, xMid ) )

        min_interior = utils.my_round(self.dhtot + self.bit.offset)
        min_finger_width = max(1, units.abstract_to_increments(self.config.min_finger_width))

        # do left side of board
        i = xMid - neck_width

        while left > 0:
            left = max(i - width / 2, 0)
            # prevent cut of on corner
            if left - offset < offset:
                left = 0
            right = i + width / 2
            if (right - offset) > min_finger_width and (right - left) > min_interior:
                self.cuts.append(router.Cut(left, right, i))
            i -= neck_width

        # do right side of board
        i = xMid + neck_width
        while left < board_width:
            left = i - width / 2
            right = min(i + width / 2, board_width)
            # prevent cut of on corner
            if right + offset > board_width:
                right = board_width
            if (board_width - (left + offset) ) > min_finger_width and (right - left) > min_interior:
                self.cuts.append(router.Cut(left, right, i))
            i += neck_width

        # If we have only one cut the entire width of the board, then
        # the board width is too small for the bit
        if self.cuts[0].xmin == 0 and self.cuts[0].xmax == board_width:
            raise Spacing_Exception('Unable to compute a equally-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('xmin'))
        if self.config.debug:
            print('e-s cuts:')
            dump_cuts(self.cuts)

class Variable_Spaced(Base_Spacing):
    '''
    Computes variable-spaced cuts, where the center cut (always centered on
    board) is the widest, with each cut decreasing linearly as you move to the edge.

    Parameters that control the spacing are:

    Fingers: Roughly the number of full fingers on either the A or B board.
    '''
    keys = ['Fingers']

    def __init__(self, bit, boards, config):
        Base_Spacing.__init__(self, bit, boards, config)
        # eff_width is the effective width, an average of the bit width
        # and the neck width
        self.eff_width = utils.my_round(self.bit.width - self.bit.offset) + 2 * self.dhtot
        self.eff_width += self.bit.dovetail_correction()
        self.wb = self.boards[0].width // self.eff_width
        self.alpha = (self.wb + 1) % 2
        # min and max number of fingers
        self.mMin = max(3 - self.alpha, utils.my_round(math.ceil(math.sqrt(self.wb))))
        self.mMax = utils.my_round((self.wb - 1.0 + self.alpha) // 2)
        if self.mMax < self.mMin:
            raise Spacing_Exception('Unable to compute a variable-spaced'\
                                    ' joint for the board and bit parameters'\
                                    ' specified.  This is likely because'\
                                    ' the board width is too small for the'\
                                    ' bit width specified.')
        self.mDefault = (self.mMin + self.mMax) // 2

        self.params = {'Fingers':Spacing_Param(self.mMin, self.mMax, self.mDefault)}

    def set_cuts(self):
        '''
        Sets the cuts to make the joint
        '''
        board_width = self.boards[0].width
        m = self.params['Fingers'].v
        self.labels = [self.keys[0] + ':']
        self.description = 'Variable Spaced (' + self.keys[0] + ': {})'.format(m)
        # c is the ideal center-cut width
        c = self.eff_width * ((m - 1.0) * self.wb - \
                              m * (m + 1.0) + self.alpha * m) /\
            (m * m - 2.0 * m - 1.0 + self.alpha)
        # d is the ideal decrease in finger width for each finger away from center finger
        d = (c - self.eff_width) / (m - 1.0)
        # compute fingers on one side of the center and the center and store them
        # in increments.  Keep a running total of sizes.
        increments = [0] * (m + 1)
        ivals = 0
        for i in lrange(1, m + 1):
            increments[i] = max(self.bit.width, int(c - d * i))
            ivals += 2 * increments[i]
        # Set the center increment.  This takes up the slop in the rounding and increment
        # resolution.
        increments[0] = board_width - ivals
        if increments[0] < increments[1]:
            # The center increment is narrower than the adjacent increment,
            # so reset it to the adjacent increment and get rid of a finger.
            increments[0] = increments[1]
            m -= 1
        if self.config.debug:
            print('v-s increments', increments)
        # Adjustments for dovetails
        deltaP = self.bit.width + 2 * self.dhtot - self.eff_width
        deltaM = utils.my_round(self.eff_width - self.bit.neck - 2 * self.dhtot) - \
                 self.bit.dovetail_correction()
        # put a cut at the center of the board
        xMid = board_width // 2
        width = increments[0] + deltaP
        left = max(0, xMid -  width // 2)
        right = min(board_width, left + width)
        self.cuts = [router.Cut(left, right)]
        # do the remaining cuts
        do_cut = False
        for i in lrange(1, m + 1):
            if do_cut:
                width = increments[i] + deltaP
                farLeft = max(0, left - width)
                self.cuts.append(router.Cut(farLeft, left))
                farRight = min(board_width, right + width)
                self.cuts.append(router.Cut(right, farRight))
            else:
                width = increments[i] - deltaM
                farLeft = max(0, left - width)
                farRight = min(board_width, right + width)
            left = farLeft
            right = farRight
            do_cut = (not do_cut)
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('xmin'))
        if self.config.debug:
            print('v-s cuts:')
            dump_cuts(self.cuts)

class Edit_Spaced(Base_Spacing):
    '''
    Allows for user to interactively edit the cuts.
    '''
    keys = []

    def __init__(self, bit, boards, config):
        Base_Spacing.__init__(self, bit, boards, config)
        self.undo_cuts = [] # list of cuts to undo
        self.params = []

    def set_cuts(self, cuts):
        '''
        Sets cuts to the input cuts
        '''
        self.cuts = cuts
        self.labels = []
        self.description = 'Edit spacing'
        self.cursor_cut = 0
        self.active_cuts = [self.cursor_cut]
        self.undo_cuts = []

    def changes_made(self):
        '''
        Returns true if editing changes have been made
        '''
        return len(self.undo_cuts) > 0

    def get_limits(self, f):
        '''
        Returns the x-coordinate limits of the cut index f
        '''
        xmin = 0
        xmax = self.boards[0].width
        neck_width = utils.my_round(self.bit.neck)
        if f > 0:
            xmin = self.cuts[f - 1].xmax + neck_width
        if f < len(self.cuts) - 1:
            xmax = self.cuts[f + 1].xmin - neck_width
        return (xmin, xmax)

    def check_limits(self, f):
        '''
        Returns True if cut index f is within its limits, False otherwise.
        '''
        (xmin, xmax) = self.get_limits(f)
        return self.cuts[f].xmin >= xmin and self.cuts[f].xmax <= xmax

    def undo(self):
        '''
        Undoes the last change to cuts
        '''
        if len(self.undo_cuts) > 0:
            self.cuts = self.undo_cuts.pop()

    def cut_move_left(self):
        '''
        Moves the active cuts 1 increment to the left
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        delete_cut = False
        for f in self.active_cuts:
            c = self.cuts[f]
            c.xmin = max(0, c.xmin - 1)
            if c.xmax == 1:
                # note its possible for only one cut to be deleted
                delete_cut = True
            elif c.xmax == self.boards[0].width:
                # if on the right end, create a new finger if it gets too wide
                wNew = self.bit.width + 2 * self.dhtot
                w = c.xmax - c.xmin
                if w > wNew:
                    c.xmax -= 1
            else:
                c.xmax -= 1
        msg = ''
        incr = 0
        if delete_cut:
            self.cut_delete(0)
            msg = 'Deleted cut 0 '
            incr = 1
        for f in self.active_cuts:
            if self.check_limits(f):
                op.append(f + incr)
            else:
                noop.append(f + incr)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts moved: unable to move indices ' + str(noop),
                    True)
        if len(op) > 0 or delete_cut:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg += 'Moved cut indices ' + str(op) + ' to left 1 increment'
        return (msg, False)

    def cut_move_right(self):
        '''
        Moves the active cuts 1 increment to the right
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        delete_cut = False
        for f in self.active_cuts:
            c = self.cuts[f]
            c.xmax = min(self.boards[0].width, c.xmax + 1)
            if c.xmin == self.boards[0].width - 1:
                # note its possible for only one cut to be deleted
                delete_cut = True
            elif c.xmin == 0:
                # if on the left end, create a new finger if it gets too wide
                wNew = self.bit.width + 2 * self.dhtot
                w = c.xmax - c.xmin
                if w > wNew:
                    c.xmin = 1
            else:
                c.xmin += 1
        msg = ''
        incr = 0
        if delete_cut:
            f = len(self.cuts) - 1
            self.cut_delete(f)
            msg = 'Deleted cut %d ' % f
        for f in self.active_cuts:
            if self.check_limits(f):
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts moved: unable to move indices ' + str(noop),
                    True)
        if len(op) > 0 or delete_cut:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg += 'Moved cut indices ' + str(op) + ' to right 1 increment'
        return (msg, False)

    def cut_widen_left(self):
        '''
        Increases the active cuts width on the left side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmin > xmin:
                c.xmin -= 1
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts widened: unable to widen indices ' + str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = ('Widened cut indices ' + str(op) + ' on left 1 increment',
                   False)
        else:
            msg = ('Widened no cuts', True)
        return msg

    def cut_widen_right(self):
        '''
        Increases the active cuts width on the right side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmax < xmax:
                c.xmax += 1
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts widened: unable to widen indices ' + str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = ('Widened cut indices ' + str(op) + ' on right 1 increment',
                   False)
        else:
            msg = ('Widened no cuts', True)
        return msg

    def cut_trim_left(self):
        '''
        Decreases the active cuts width on the left side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            wmin = self.bit.width + 2 * self.dhtot
            if c.xmax == self.boards[0].width:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                noop.append(f)
            else:
                c.xmin += 1
                self.cuts[f] = c
                op.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts trimmed: unable to trim indices ' + str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = ('Trimmed cut indices ' + str(op) + ' on left 1 increment',
                   False)
        else:
            msg = ('Trimmed no cuts', True)
        return msg

    def cut_trim_right(self):
        '''
        Decreases the active cuts width on the right side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            wmin = self.bit.width + 2 * self.dhtot
            if c.xmin == 0:
                wmin = 1
            if c.xmax - c.xmin <= wmin:
                noop.append(f)
            else:
                c.xmax -= 1
                self.cuts[f] = c
                op.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return ('No cuts trimmed: unable to trim indices ' + str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = ('Trimmed cut indices ' + str(op) + ' on right 1 increment',
                   False)
        else:
            msg = ('Trimmed no cuts', True)
        return msg

    def cut_increment_cursor(self, inc):
        '''
        Increments the cursor cut, cyclicly.  Increment can be positive or negative.
        '''
        self.cursor_cut = (self.cursor_cut + inc) % len(self.cuts)
        return 'Moved cut cursor to cut index %d' % self.cursor_cut

    def cut_toggle(self):
        '''
        Toggles Increments the cursor cut, cyclicly.  Increment can be positive or negative.
        '''
        if self.cursor_cut in self.active_cuts:
            self.active_cuts.remove(self.cursor_cut)
            msg = 'Deactivated cut index %d' % self.cursor_cut
        else:
            self.active_cuts.append(self.cursor_cut)
            msg = 'Activated cut index %d' % self.cursor_cut
        return msg

    def cut_all_active(self):
        '''
        Sets all cuts as active.
        '''
        self.active_cuts = lrange(len(self.cuts))
        return 'All cuts activated'

    def cut_all_not_active(self):
        '''
        Deactivate all cuts.
        '''
        self.active_cuts = []
        return 'All cuts deactivated'

    def cut_delete(self, f):
        '''
        Deletes cut of index f.  Returns True if able to delete the cut,
        False otherwise.
        '''
        if len(self.cuts) < 2: # don't delete the last cut
            return False
        # delete from the cuts list
        c = self.cuts[0:f]
        c.extend(self.cuts[f + 1:])
        self.cuts = c
        # adjust the cursor appropriately
        if self.cursor_cut >= f and self.cursor_cut > 0:
            self.cursor_cut -= 1
        # adjust the active cuts list
        id = self.active_cuts.index(f)
        c = self.active_cuts[0:id]
        c.extend(self.active_cuts[id + 1:])
        self.active_cuts = c
        for i in lrange(len(self.active_cuts)):
            if self.active_cuts[i] > f:
                self.active_cuts[i] -= 1
        return True

    def cut_delete_active(self):
        '''
        Deletes the active cuts.
        '''
        cuts_save = copy.deepcopy(self.cuts)
        deleted = []
        failed = False
        # delete in reverse order, so that modifications to cuts don't affect index values
        rev = sorted(self.active_cuts, reverse=True)
        for f in rev:
            if not self.cut_delete(f):
                failed = True
                break
            deleted.append(f)
        self.active_cuts = [self.cursor_cut]
        if len(deleted) > 0:
            msg = 'Deleted cut indices ' + str(deleted)
            self.undo_cuts.append(cuts_save)
        else:
            msg = 'Deleted no cuts'
        if failed:
            msg += '; unable to delete last cut'
        return (msg, failed)

    def cut_add(self):
        '''
        Adds a cut to the first location possible, searching from the left.
        The active cut is set the the new cut.
        '''
        neck_width = utils.my_round(self.bit.neck)
        index = None
        cuts_save = copy.deepcopy(self.cuts)
        if self.cuts[0].xmin > self.bit.neck:
            if self.config.debug:
                print('add at left')
            index = 0
            xmin = 0
            xmax = self.cuts[0].xmin - neck_width
        wadd = 2 * self.bit.width + neck_width
        wdelta = self.bit.width - neck_width
        for i in lrange(1, len(self.cuts)):
            if self.cuts[i].xmin - self.cuts[i - 1].xmax + wdelta >= wadd:
                if self.config.debug:
                    print('add in cut')
                index = i
                xmin = self.cuts[i - 1].xmax + neck_width
                xmax = xmin + self.bit.width
                break
            elif self.cuts[i].xmax - self.cuts[i].xmin >= wadd:
                if self.config.debug:
                    print('add in cut')
                index = i + 1
                xmin = self.cuts[i].xmax - self.bit.width
                xmax = self.cuts[i].xmax
                self.cuts[i].xmax = self.cuts[i].xmin + self.bit.width
                break
        if index is None and \
           self.cuts[-1].xmax < self.boards[0].width - self.bit.neck:
            if self.config.debug:
                print('add at right')
            index = len(self.cuts)
            xmax = self.boards[0].width
            xmin = self.cuts[-1].xmax + neck_width
        if index is None:
            return ('Unable to add cut', True)
        self.undo_cuts.append(cuts_save)
        c = self.cuts[0:index]
        c.append(router.Cut(xmin, xmax))
        c.extend(self.cuts[index:])
        self.cuts = c
        self.cursor_cut = index
        self.active_cuts = [index]
        return ('Added cut', False)
