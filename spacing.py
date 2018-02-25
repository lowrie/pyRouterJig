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
    '''Dumps the cuts to the screen...this is for debugging
    in column form.
    '''
    print('Min\tMax')
    for c in cuts:
        print('{:f}\t{:f}'.format(c.xmin, c.xmax))


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
        self.description = 'NONE'
        self.bit = bit
        self.boards = boards
        self.config = config
        self.cursor_cut = None
        self.active_cuts = []
        self.cuts = []
        self.labels = []
        self.transl = bit.units.transl

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
    msg = 'Unable to compute a equally-spaced'\
          ' joint for the board and bit parameters'\
          ' specified.  This is likely because'\
          ' the board width is too small for the'\
          ' bit width specified.'

    def is_board_width_ok(bit, boards, config):
        dhtot = boards[2].dheight * boards[2].active + boards[3].dheight * boards[3].active
        mMax = bit.width + dhtot +   int((boards[0].width // (bit.midline + dhtot)) // 2 + 1) \
               + max(1, bit.units.abstract_to_increments(config.min_finger_width)) * 2
        return mMax <= boards[0].width

    def __init__(self, bit, boards, config):
        Base_Spacing.__init__(self, bit, boards, config)

        dh2 = 2 * self.dhtot
        t = [Spacing_Param(0, self.boards[0].width // 4 + dh2, 0),
             Spacing_Param(self.bit.midline + dh2, self.boards[0].width // 2 + dh2,
                           self.bit.midline + dh2),
             Spacing_Param(None, None, True)]
        self.params = {}
        for i in lrange(len(t)):
            self.params[self.keys[i]] = t[i]

    def set_cuts(self):
        '''
        Sets the cuts to make the joint
        '''

        # on local variables init 
        # we have to care about imperial values and convert them to increments before use
        spacing = self.params['Spacing'].v
        width = Decimal(math.floor(self.params['Width'].v))

        if not self.bit.units.metric and width < 1.:
            spacing = self.bit.units.inches_to_increments(self.params['Spacing'].v)
            width = Decimal(math.floor(self.bit.units.inches_to_increments(self.params['Width'].v)))

        shift = Decimal(self.bit.midline % 2) / 2  # offset to keep cut center mm count
        centered = self.params['Centered'].v
        neck_width = width + spacing
        overhang = self.bit.overhang

        board_width = self.boards[0].width
        units = self.bit.units
        label = units.increments_to_string(spacing, True)

        min_interior = utils.my_round(self.dhtot + self.bit.overhang)
        # min_finger_width means most thin wood at the corner
        min_finger_width = max(1, units.abstract_to_increments(self.config.min_finger_width))

        if centered or \
           self.bit.angle > 0:  # always symm. for dovetail
            # put a cut at the center of the board with half of inctrmrnt prec.
            xMid = Decimal(board_width // 2) - shift + (width % 2) / 2
            left = Decimal(max(0, xMid - width / 2))
        else:
            # keep corner finger and groove equality on the board edges
            left = (board_width % (width + neck_width)) // 2
            if (left - overhang) < min_finger_width:
                left = 0

        # Note the Width slider measures "midline" but indicates the actual cut space
        # show actual maximum cut with for dovetails
        self.labels = self.keys[:]
        l0 = self.transl.tr(self.labels[0])
        l1 = self.transl.tr(self.labels[1])
        self.labels[2] = self.transl.tr(self.labels[2])
        self.labels[0] = l0 +': ' + label
        self.labels[1] = l1 +': ' + units.increments_to_string(width + overhang * 2, True)
        self.description = self.transl.tr('Equally spaced ')+' (' + self.labels[0] + \
                           ', ' + self.labels[1] + ')'
        self.cuts = []  # return value

        right = Decimal(min(board_width, left + width))
        self.cuts.append(router.Cut(left - overhang, right + overhang))

        # do left side of board
        i = left

        while left > 0:
            i -= neck_width
            left = i - width

            # prevent thin first cut
            if left < min_finger_width:
                left = 0
            if (i - overhang) > min_finger_width and (i - left - overhang * 2) > min_interior:
                self.cuts.append(router.Cut(max(0, left - overhang), i + overhang))
            i = left

        # do right side of board
        i = right
        while right < board_width:
            i += neck_width
            right = i + width
            # prevent thin last cut
            # devetail may cut off corner finger
            if (board_width - right) < min_finger_width:
                right = board_width
            if (board_width - i + overhang) > min_finger_width and (right - i - overhang * 2) > min_interior:
                self.cuts.append(router.Cut(i - overhang, min(board_width, right + overhang)))
            i = right

        # If we have only one cut the entire width of the board, then
        # the board width is too small for the bit
        if self.cuts[0].xmin == 0 and self.cuts[0].xmax == board_width:
            raise Spacing_Exception(self.transl.tr(Equally_Spaced.msg))
        # sort the cuts in increasing x
        self.cuts = sorted(self.cuts, key=attrgetter('xmin'))
        if self.config.debug:
            print('e-s cuts:')
            dump_cuts(self.cuts)


class Variable_Spaced(Base_Spacing):
    '''
    Computes variable-spaced cuts, where the center cut (always centered on
    board) is the widest, with each cut decreasing linearly as you move to the edge.
    arithmetical progression wirks just fine for such task
    Parameters that control the spacing are:

    Fingers: Roughly the number of full fingers on either the A or B board.
    '''
    keys = ['Fingers','Spacing','Inverted']
    msg = \
        'Unable to compute a variable-spaced'\
        ' joint for the board and bit parameters'\
        ' specified.  This is likely because'\
        ' the board width is too small for the'\
        ' bit width specified.'

    @staticmethod
    def is_board_width_ok(bit, boards):
        mMin = 3
        dhtot = boards[2].dheight * boards[2].active + boards[3].dheight * boards[3].active
        mMax = int((boards[0].width // (bit.midline + dhtot)) // 2 + 1)
        return mMax > mMin

    def __init__(self, bit, boards, config):
        Base_Spacing.__init__(self, bit, boards, config)

        # min and max number of fingers
        # we actually can set 2 fingers but tests does not pass this value
        self.mMin = 3
        self.mMax = int((self.boards[0].width // (self.bit.midline + self.dhtot)) // 2 + 1)
        units = self.bit.units
        self.min_interior = 0
        if self.mMax < self.mMin:
            # we try to survive here.., Normally it's better to call is_board_width_ok prior create the object
            raise Spacing_Exception(units.transl.tr(Variable_Spaced.msg))

        self.mDefault = (self.mMin + self.mMax) // 2
        self.params = {Variable_Spaced.keys[0]: Spacing_Param(self.mMin, self.mMax, self.mDefault),
                       Variable_Spaced.keys[1]: Spacing_Param(0, 7, 4),
                       Variable_Spaced.keys[2]: Spacing_Param(0, 0, False)}
        self.calc_var_params()

    def calc_var_params(self):
        '''
        Calculate paramiters forVariable cuts
        Call of this function must forboard width, bit, number of fingers, inverse
        :return:
        '''
        min_interior = self.bit.midline + self.dhtot * 2
        S = math.floor( Decimal(self.boards[0].width) / 2)    # half board width
        n = int(self.params['Fingers'].v)  # number of cuts
        d = 0  # d is the ideal decrease in finger width for each finger away from center finger
        an = 0
        over = 0

        # Iterate to get perfect d value
        if self.params['Inverted'].v == False :
            while an <=0  or ((an + over) > 4 and (an - d) >= min_interior) :
                d += -1
                a1 = utils.math_round(((2 * S) - (n - 1) * n * d) / Decimal(2 * n - 1))
                an = a1 + Decimal(n - 1) * d
                over = (S + a1 // 2) - ((a1 + an) * n) // 2
        else:
            a1 = min_interior
            while  a1 >= min_interior:
                d += 1
                a1 = utils.math_round(((2 * S) - (n - 1) * n * d) / Decimal(2 * n - 1))
                an = a1 + Decimal(n - 2) * d
                over =  S - ((a1 + an) * n) // 2
            d -= 1

        d = abs(d)
        self.params['Spacing'].vMax = d
        if self.params['Spacing'].v >= d:
            self.params['Spacing'].v = d

    def set_cuts(self):
        '''
        Sets the cuts to make the joint
        S - progression summary (half length of the board)
        n - number of fingers (actually number of parts per half of the board)
        d -  the difference between terms of the arithmetic progression
        a1 - first cut width (it must be symmetric at center of the board)
        an - the last cut or finger
        because a1 is at the board center we got:
        S = (n * 2*a1+(n-1) * d / 2 - a1/2
        from this equation we solve a1
        a1 = ( (2 * S) - (n - 1) * n * d ) / (2 * n - 1)
        the next task is to find the best possible d (I love big numbers)
        '''
        S = math.floor( Decimal(self.boards[0].width) / 2)    # half board width
        n = int(self.params['Fingers'].v)  # number of cuts
        d = int(self.params['Spacing'].v)  # d is the ideal decrease in finger width for each finger away from center finger
        overhang = self.bit.overhang  # offset from midline to the end of cut

        units = self.bit.units
        min_interior = self.bit.midline + self.dhtot * 2
        min_finger_width = Decimal(self.bit.units.abstract_to_increments(self.config.min_finger_width) + self.dhtot)
        min_interior = self.bit.midline + self.dhtot * 2
        shift = Decimal((self.bit.midline) % 2) / 2   # offset to keep cut senter

        # Iterate to get perfect d value
        if self.params['Inverted'].v == False :
            d= -d
        a1 = utils.math_round(((2 * S) - (n - 1) * n * d) / Decimal(2 * n - 1))
        a1 = max(a1, min_interior)
        an = a1 + Decimal(n - 1) * d
        an = round(an,0)
        SP = (a1 + d + an) * (n - 1) + a1
        delta = self.boards[0].width - SP

        # compute fingers on one side of the center and the center and store them
        # in increments.  Keep a running total of sizes.
        increments = [Decimal(0)] * int(n)
        for i in lrange(0, n):
            increments[i] = a1 + d * i
            if increments[i] < min_interior:
                increments[i] = min_interior

        # wide last cut
        if abs(delta) >= 2:
            increments[-1] += delta // 2
            delta -= (delta // 2) * 2

        # wide center cut in case the delta is a 1 increment
        if abs(delta) == 1:
            increments[0] += delta

        if increments[-1] > increments[-2]:
            increments[-1] = increments[-2]

        if self.config.debug:
            print('v-s increments', increments)

        # put a cut at the center of the board
        xMid = S + shift - Decimal(increments[0] % 2) / 2
        neck = Decimal(increments[0]) / 2
        left = xMid - neck
        right = xMid + neck
        self.labels = [units.transl.tr(self.keys[0]), units.transl.tr(self.keys[1]) +': '+ str(d), self.keys[2]]
        self.description = units.transl.tr('Variable Spaced ( {}: {})')\
                               .format(units.transl.tr(self.keys[0]), n)

        self.cuts = [router.Cut(left - overhang, right + overhang)]

        do_cut = False
        for i in lrange(1, n):
            if do_cut:
                # cut width
                l_left = left - increments[i] - overhang
                r_right = right + increments[i] + overhang
                # prevent thin cuts
                if l_left < min_finger_width:
                    l_left = 0
                if (self.boards[0].width - r_right) < min_finger_width:
                    r_right = self.boards[0].width
                self.cuts.append(router.Cut(max(0, l_left), left + overhang))
                self.cuts.append(router.Cut(right - overhang, r_right))

            left -= increments[i]
            right += increments[i]
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
        self.undo_cuts = []  # list of cuts to undo
        self.params = []

    def set_cuts(self, cuts):
        '''
        Sets cuts to the input cuts
        '''
        self.cuts = cuts
        self.labels = []
        self.description = self.transl.tr('Edit spacing')
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
        midline = utils.my_round(self.bit.midline)
        overhang = self.bit.overhang
        if f > 0:
            xmin = self.cuts[f - 1].xmax + midline - overhang * 2
        if f < len(self.cuts) - 1:
            xmax = self.cuts[f + 1].xmin - midline + overhang * 2
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
        with min finger with respect
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)
        delete_cut = False
        for f in self.active_cuts:
            c = self.cuts[f]
            c.xmin -= 1
            if c.xmin <= min_finger_width:
                c.xmin = 0
            if (c.xmax - self.bit.overhang) <= min_finger_width:
                # note its possible for only one cut to be deleted
                delete_cut = True
            elif c.xmax == self.boards[0].width:
                # if on the right end, create a new finger if it gets too wide
                wNew = self.bit.midline + (self.dhtot + self.bit.overhang) * 2
                w = c.xmax - c.xmin
                if (w - wNew) >= min_finger_width:
                    c.xmax = c.xmin + (self.dhtot * 2 + self.bit.width_f)
            else:
                c.xmax -= 1
        msg = ''
        incr = 0
        if delete_cut:
            self.cut_delete(0)
            msg = self.transl.tr('Deleted cut 0 ')
            incr = 1
        for f in self.active_cuts:
            if self.check_limits(f):
                op.append(f + incr)
            else:
                noop.append(f + incr)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts moved: unable to move indices %s') % str(noop),
                    True)
        if len(op) > 0 or delete_cut:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg += self.transl.tr('Moved cut indices %s to left 1 increment') % str(op)
        return (msg, False)

    def cut_move_right(self):
        '''
        Moves the active cuts 1 increment to the right
        with min finger with respect
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        delete_cut = False
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)

        for f in self.active_cuts:
            c = self.cuts[f]
            c.xmax += 1
            if self.boards[0].width - c.xmax < min_finger_width:
                c.xmax = self.boards[0].width
            if (c.xmin + self.bit.overhang + min_finger_width) >= self.boards[0].width:
                # note its possible for only one cut to be deleted
                delete_cut = True
            elif c.xmin == 0:
                # if on the left end, create a new finger if it gets too wide
                wNew = self.bit.midline + (self.dhtot + self.bit.overhang) * 2
                w = c.xmax - c.xmin
                if (w - wNew) >= min_finger_width:
                    c.xmin = c.xmax - (self.dhtot * 2 + self.bit.width_f)
            else:
                c.xmin += 1
        msg = ''
        if delete_cut:
            f = len(self.cuts) - 1
            self.cut_delete(f)
            msg = self.transl.tr('Deleted cut %d ') % f
        for f in self.active_cuts:
            if self.check_limits(f):
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts moved: unable to move indices %s') % str(noop),
                    True)
        if len(op) > 0 or delete_cut:
            self.undo_cuts.append(cuts_save)
        if len(op) > 0:
            msg += self.transl.tr('Moved cut indices %s to right 1 increment') % str(op)
        return (msg, False)

    def cut_widen_left(self):
        '''
        Increases the active cuts width on the left side by 1 increment
        '''
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmin > xmin:
                c.xmin -= 1
                if c.xmin < min_finger_width:
                    c.xmin = 0
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts widened: unable to widen indices %s') % str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = (self.transl.tr('Widened cut indices %s on left 1 increment') % str(op),
                   False)
        else:
            msg = (self.transl.tr('Widened no cuts'), True)
        return msg

    def cut_widen_right(self):
        '''
        Increases the active cuts width on the right side by 1 increment
        '''
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        for f in self.active_cuts:
            c = self.cuts[f]
            (xmin, xmax) = self.get_limits(f)
            if c.xmax < xmax:
                c.xmax += 1
                if self.boards[0].width - c.xmax < min_finger_width:
                    c.xmax = self.boards[0].width
                self.cuts[f] = c
                op.append(f)
            else:
                noop.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts widened: unable to widen indices %s') % str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = (self.transl.tr('Widened cut indices %s on right 1 increment') % str(op),
                   False)
        else:
            msg = (self.transl.tr('Widened no cuts'), True)
        return msg

    def cut_trim_left(self):
        '''
        Decreases the active cuts width on the left side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)

        for f in self.active_cuts:
            c = self.cuts[f]
            wmin = self.bit.width_f + 2 * self.dhtot
            if c.xmin == 0:
                c.xmin = max(0, c.xmax - self.bit.width_f - 2 * self.dhtot)
                if c.xmin < min_finger_width:
                    c.xmin = 0
            else:
                c.xmin += 1

            if c.xmax < self.boards[0].width and c.xmin > 0 and (c.xmax - c.xmin) < wmin:
                    noop.append(f)
            else:
                self.cuts[f] = c
                op.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts trimmed: unable to trim indices %s') % str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = (self.transl.tr('Trimmed cut indices %s on left 1 increment') % str(op),
                   False)
        else:
            msg = (self.transl.tr('Trimmed no cuts'), True)
        return msg

    def cut_trim_right(self):
        '''
        Decreases the active cuts width on the right side by 1 increment
        '''
        cuts_save = copy.deepcopy(self.cuts)
        op = []
        noop = []
        min_finger_width = self.bit.units.abstract_to_increments(self.config.min_finger_width)

        for f in self.active_cuts:
            c = self.cuts[f]
            wmin = self.bit.width_f + 2 * self.dhtot
            if c.xmax == self.boards[0].width:
                c.xmax = min(self.boards[0].width, c.xmin + self.bit.width_f + 2 * self.dhtot)
                if self.boards[0].width - c.xmax < min_finger_width:
                    c.xmax = self.boards[0].width
            else:
                c.xmax -= 1
            if c.xmax < self.boards[0].width and c.xmin > 0 and (c.xmax - c.xmin) < wmin:
                noop.append(f)
            else :
                self.cuts[f] = c
                op.append(f)
        if len(noop) > 0:
            self.cuts = cuts_save
            return (self.transl.tr('No cuts trimmed: unable to trim indices %s') % str(noop),
                    True)
        if len(op) > 0:
            self.undo_cuts.append(cuts_save)
            msg = (self.transl.tr('Trimmed cut indices %s on right 1 increment') % str(op),
                   False)
        else:
            msg = (self.transl.tr('Trimmed no cuts'), True)
        return msg

    def cut_increment_cursor(self, inc):
        '''
        Increments the cursor cut, cyclicly.  Increment can be positive or negative.
        '''
        self.cursor_cut = (self.cursor_cut + inc) % len(self.cuts)
        return self.transl.tr('Moved cut cursor to cut index %d') % self.cursor_cut

    def cut_toggle(self):
        '''
        Toggles Increments the cursor cut, cyclicly.  Increment can be positive or negative.
        '''
        if self.cursor_cut in self.active_cuts:
            self.active_cuts.remove(self.cursor_cut)
            msg = self.transl.tr('Deactivated cut index %d') % self.cursor_cut
        else:
            self.active_cuts.append(self.cursor_cut)
            msg = self.transl.tr('Activated cut index %d') % self.cursor_cut
        return msg

    def cut_all_active(self):
        '''
        Sets all cuts as active.
        '''
        self.active_cuts = lrange(len(self.cuts))
        return self.transl.tr('All cuts activated')

    def cut_all_not_active(self):
        '''
        Deactivate all cuts.
        '''
        self.active_cuts = []
        return self.transl.tr('All cuts deactivated')

    def cut_delete(self, f):
        '''
        Deletes cut of index f.  Returns True if able to delete the cut,
        False otherwise.
        '''
        if len(self.cuts) < 2:  # don't delete the last cut
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
        overhang = self.bit.overhang
        midline = self.bit.midline
        index = None
        cuts_save = copy.deepcopy(self.cuts)
        min_finger_width = math.floor(self.bit.units.abstract_to_increments(self.config.min_finger_width)) + 1
        wadd = min_finger_width + self.dhtot
        xmin = 0
        xmax = 0
        if self.cuts[0].xmin > self.bit.midline - overhang + wadd:
            if self.config.debug:
                print('add at left')
            index = 0
            xmin = 0
            xmax = xmin + wadd + overhang

        wadd = 2 * (self.bit.midline + self.dhtot)
        wdelta = overhang * 2

        for i in lrange(1, len(self.cuts)):
            if self.cuts[i].xmin - self.cuts[i - 1].xmax + wdelta >= wadd + self.bit.midline:
                if self.config.debug:
                    print('add in cut')
                index = i
                xmin = self.cuts[i - 1].xmax - overhang + midline
                xmax = xmin + self.bit.midline + overhang + 2 * self.dhtot
                xmin -= overhang
                break

            elif (self.cuts[i].xmax - self.cuts[i].xmin - wdelta) >= wadd + self.bit.midline:
                if self.config.debug:
                    print('add in cut')
                index = i + 1
                xmax = self.cuts[i].xmin + self.bit.midline + (overhang + self.dhtot) * 2
                xmin = xmax + self.bit.midline - 2 * overhang
                t = self.cuts[i].xmax
                self.cuts[i].xmax = xmax
                xmax = t
                break
        if index is None and \
           self.cuts[-1].xmax < self.boards[0].width - overhang:
            if self.config.debug:
                print('add at right')
            index = len(self.cuts)
            xmax = self.boards[0].width
            xmin = self.cuts[-1].xmax - overhang
        if index is None:
            return (self.transl.tr('Unable to add cut'), True)
        self.undo_cuts.append(cuts_save)
        c = self.cuts[0:index]
        c.append(router.Cut(xmin, xmax))
        c.extend(self.cuts[index:])
        self.cuts = c
        self.cursor_cut = index
        self.active_cuts = [index]
        return (self.transl.tr('Added cut'), False)
