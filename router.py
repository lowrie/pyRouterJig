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
Contains the router, board, template and their geometry properties.
'''

from decimal import Decimal as D
from decimal import ROUND_HALF_DOWN
import math
import utils


class Router_Exception(Exception):
    '''
    Exception handler for all routerJig
    '''
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return self.msg

class Incra_Template(object):
    '''
    Contains properties of an incra template

    Attributes:

    height: Dimension in y-coordinate
    margin: Dimension in x-coordinate placed on each end of template
    length: total length of template
    '''
    def __init__(self, units, boards, margin=None, length=None):
        # incra uses 1/2" high templates
        self.height = units.inches_to_increments(0.5)
        self.transl = units.transl
        if margin is None:
            self.margin = units.inches_to_increments(1.0)
        else:
            self.margin = margin
        if length is None:
            self.length = boards[0].width + 2 * self.margin
        else:
            self.length = length

class Router_Bit(object):
    '''
    Stores properties of dovetail and straight router bits.

    Input attributes (after creation, use setter functions to set these)

    angle: (float) measured from y-axis, in degrees, following dovetail bit
           standard. Zero for straight bit.

    width: (integer) max cutting width.  This is the bottom of a dovetail bit.
           For now, this must be an even number.

    depth: (float) cutting depth. Equals board thickness for through dovetails
           and box joints.

    Computed attributes:

    offset: (float) x-dimension between max-width point and point at board's
            surface.  Zero for angle=0.

    neck: width of bit at board surface.

    midline: disstance between cuts in incremental units

    depth_0: optimal depth with perfect fit

    width_f: perfect width with no rounding

    gap: the calculated disstance to perfect fit value

    halfwidth: half of width
    '''
    def __init__(self, units, width, depth, angle=0, bit_gentle=33.):
        self.units = units
        self.transl = units.transl
        self.width = width
        self.depth = depth
        self.angle = angle
        self.bit_gentle = D(bit_gentle)

        self.midline = D('0')
        self.depth_0 = D('0')
        self.width_f = D(repr(width))
        self.overhang = (self.width_f - self.midline) / 2
        self.gap = D('0')

        self.reinit()

    def set_gentle_from_string(self, s):
        '''
        Sets the width from the string s, following requirements from units.string_to_increments().
        '''
        msg = self.transl.tr('Unable to set gentle to: {}<p>'\
              'Set to a positive value from 1 to 100%, such as: {}').format(s, 33.3)
        try:
            bit_gentle = self.units.string_to_float(s)
            if bit_gentle < 1 or bit_gentle > 100:
                raise()
        except:
            raise Router_Exception(msg)

        self.bit_gentle = D(s)
        self.reinit()

    def set_width_from_string(self, s):
        '''
        Sets the width from the string s, following requirements from units.string_to_increments().
        '''
        if self.units.metric:
            val = '6'
        else:
            val = '1/2'
        msg = self.transl.tr('Unable to set Bit Width to: {}<p>'\
              'Set to a positive value, such as: {}').format(s, val)
        try:
            if self.units.metric:
                width = self.units.string_to_float(s)
                if width <= 1:
                    width *= self.units.mm_per_inch
            else:
                width = self.units.string_to_increments(s)
        except:
            raise Router_Exception(msg)
        if width <= 0:
            raise Router_Exception(msg)

        halfwidth = width // 2
        if (2 * halfwidth != width or math.floor(width) != width) and self.angle == 0:
            msg += self.transl.tr('<p>Stright Bit Width must be an even number of increments.<p>'\
                   'The increment size is: {}<p>'\
                   '').format(self.units.increments_to_string(1, True))
            raise Router_Exception(msg)

        self.width = width
        self.reinit()

    def set_depth_from_string(self, s):
        '''
        Sets the depth from the string s, following requirements from units.string_to_increments().
        '''
        if self.units.metric:
            val = '5'
        else:
            val = '3/4'
        msg = self.transl.tr('Unable to set Bit Depth to: {}<p>'\
              'Set to a positive value, such as: {}').format(s, val)
        try:
            depth = self.units.string_to_increments(s, False)
            if self.angle > 0 and round( (self.width / 3.5 ) / math.tan(math.radians(self.angle)) <= depth) :
                val = round((self.width / 3.5 ) / math.tan(math.radians(self.angle)))
                msg = self.transl.tr('Unable to set Bit Depth to: {}<p>'\
                                     'The maximum depth of cut is not more than: {}').format(s, val)
                raise ValueError()
        except:
            raise Router_Exception(msg)
        if depth <= 0:
            raise Router_Exception(msg)
        self.depth = depth
        self.reinit()

    def set_angle_from_string(self, s):
        '''
        Sets the angle from the string s, where s represents a floating point number or fractional number.
        '''
        msg = self.transl.tr('Unable to set Bit Angle to: {}<p>'\
              'Set to zero or a positive value, such as 7.5 or "7 1/2"').format(s)
        try:
            angle = self.units.string_to_float(s)
            if angle == 0 and math.floor(self.width_f) != self.width_f:
                msg = self.transl.tr('Unable to set Bit Angle to: 0<p>' \
                      'Change Bit Width to odd value first <p>'\
                      'than drop angle to 0 to get stright bit')
                raise()
        except:
            raise Router_Exception(msg)
        if angle < 0:
            raise Router_Exception(msg)
        self.angle = angle
        self.reinit()

    def reinit(self):
        '''
        Reinitializes internal attributes that are dependent on width
        and angle.
        '''
        self.midline = D(repr(self.width))
        self.depth_0 = D(repr(self.depth))
        self.width_f = D(repr(self.width))
        self.gap = D('0')

        if self.angle > 0:
            tan = D(math.tan(math.radians(self.angle)))
            offset = D(self.depth) * tan
            self.midline = self.width_f - offset
            midline = self.midline.to_integral_value(rounding=ROUND_HALF_DOWN)
            self.gap = D(self.midline) - midline
            self.midline = midline
            self.depth_0 = (self.width_f - self.midline) / tan

        self.overhang = (self.width_f - self.midline) / 2


class My_Rectangle(object):
    '''
    Stores a rectangle geometry
    '''
    def __init__(self, xOrg, yOrg, width, height):
        '''
        (xOrg, yOrg): Bottom-left coordinate (origin)
        width: Extent in s
        height: Extent in y
        '''
        self.set_origin(xOrg, yOrg)
        self.width = width
        self.height = height

    def xMid(self):
        '''Returns the x-coordinate of the midpoint.'''
        return self.xOrg + self.width // 2

    def yMid(self):
        '''Returns the y-coordinate of the midpoint.'''
        return self.yOrg + self.height // 2

    def xL(self):
        '''Returns the left (min) x-coordindate'''
        return self.xOrg

    def xR(self):
        '''Returns the right (max) x-coordindate'''
        return self.xOrg + self.width

    def yB(self):
        '''Returns the bottom (min) y-coordindate'''
        return self.yOrg

    def yT(self):
        '''Returns the top (max) y-coordindate'''
        return self.yOrg + self.height

    def set_origin(self, xOrg, yOrg):
        '''Sets the origin to xs, ys'''
        self.xOrg = xOrg
        self.yOrg = yOrg


class Board(My_Rectangle):
    '''
    Board of wood description.

    Attributes:
    units: Units object
    width: Dimension of routed edge (along x-axis)
    height: Dimension perpendicular to routed edge (along y-axis)
    thickness: Dimension into paper or screen (not used yet)
    wood: Wood image used for fill
    active: If true, this board is active

    Dimensions are in increment units.
    '''
    def __init__(self, bit, width, thickness=32):
        My_Rectangle.__init__(self, 0, 0, width, 32)
        self.units = bit.units
        self.thickness = thickness
        self.wood = None
        self.active = True
        self.dheight = 0
        self.set_height(bit)
        self.bottom_cuts = None
        self.top_cuts = None
        self.transl = bit.units.transl

    def set_wood(self, wood):
        '''Sets attribute wood'''
        self.wood = wood

    def set_active(self, active=True):
        '''Sets attribute active'''
        self.active = active

    def set_width_from_string(self, s):
        '''
        Sets the width from the string s, following requirements from units.string_to_increments().
        '''
        if self.units.metric:
            val = '42' # recomend to use the answer for all questions
            maxw = 1000 # set limit to with 1 meter
        else:
            val = '7 1/2'
            maxw = 32 * 48 # set 4 feet limitation to with

        msg = self.transl.tr('Unable to set Board Width to: {}<p>'\
              'Set to a postive value less then 4 feet (1 meter) , such as: {}').format(s, val)
        try:
            width = self.units.string_to_increments(s)
        except:
            raise Router_Exception(msg)
        if width <= 0 or width > maxw:
            raise Router_Exception(msg)
        self.width = width

    def set_height(self, bit, dheight=None):
        '''
        Sets the height from the router bit depth of cut
        '''
        if dheight is None:
            if self.dheight > 0:
                h = self.dheight
            else:
                h = utils.my_round(0.5 * bit.depth)
        else:
            self.dheight = dheight
            h = dheight
        self.height = bit.depth + h

    def set_height_from_string(self, bit, s):
        '''
        Sets the height from the string s, following requirements from units.string_to_increments().
        This sets the attribute dheight, which is the increment above the bit depth.
        '''
        # TODO: This is called "thickness" because we set this only for
        # double* boards, for which we call this the thickness.
        if self.units.metric:
            val = '4'
        else:
            val = '1/8'
        msg = self.transl.tr('Unable to set board Thickness to: {}<p>'\
              'Set to a postive value, such as: {}').format(s, val)
        try:
            t = self.units.string_to_increments(s)
        except:
            raise Router_Exception(msg)
        if t <= 0:
            raise Router_Exception(msg)
        self.set_height(bit, t)

    def set_bottom_cuts(self, cuts, bit):
        '''Sets the bottom cuts for the board'''
        for c in cuts:
            c.make_router_passes(bit, self)
        self.bottom_cuts = cuts

    def set_top_cuts(self, cuts, bit):
        '''Sets the top cuts for the board'''
        for c in cuts:
            c.make_router_passes(bit, self)
        self.top_cuts = cuts

    def _do_cuts(self, bit, cuts, y_nocut, y_cut):
        '''Creates the perimeter coordinates for the given cuts'''
        x = []
        y = []
        halfgap = bit.gap / 2
        overhang = 2 * bit.overhang

        if cuts[0].xmin > 0:
            x = [D(self.xL())]
            y = [D(y_nocut)]
        # loop through the cuts and add them to the perimeter
        for c in cuts:
            if c.xmin > 0:
                # on the surface, start of cut
                x.append(c.xmin + x[0] + overhang - halfgap)
                y.append(D(y_nocut))
            # at the cut depth, start of cut
            x.append(c.xmin + self.xL() - halfgap)
            y.append(D(y_cut))
            # at the cut depth, end of cut
            x.append(c.xmax + self.xL() + halfgap)
            y.append(D(y_cut))
            if c.xmax < self.width:
                # at the surface, end of cut
                x.append(c.xmax + self.xL() - overhang + halfgap)
                y.append(D(y_nocut))
        # add the last point on the top and bottom, at the right edge,
        # accounting for whether the last cut includes this edge or not.
        if cuts[-1].xmax < self.width:
            x.append(self.xL() + self.width)
            y.append(D(y_nocut))
        return (x, y)

    def do_all_cuts(self, bit):
        '''
        Returns (xtop, ytop, xbottom, ybottom), which are the coordinates of the top and
        bottom cuts, ordered left to right.  If the edge has no cuts, just the endpoints
        of the board are returned.
        '''
        # Do the top edge
        y_nocut = self.yT()  # y-location of uncut edge
        if self.top_cuts is None:
            xtop = [self.xL(), self.xR()]
            ytop = [y_nocut, y_nocut]
        else:
            y_cut = y_nocut - bit.depth   # y-location of routed edge
            (xtop, ytop) = self._do_cuts(bit, self.top_cuts, y_nocut, y_cut)
        # Do the bottom edge
        y_nocut = self.yB()  # y-location of uncut edge
        if self.bottom_cuts is None:
            xb = [self.xL(), self.xR()]
            yb = [y_nocut, y_nocut]
        else:
            y_cut = y_nocut + bit.depth   # y-location of routed edge
            (xb, yb) = self._do_cuts(bit, self.bottom_cuts, y_nocut, y_cut)
        return (xtop, ytop, xb, yb)

    def perimeter(self, bit):
        '''
        Compute the perimeter coordinates of the board.

        bit: A Router_Bit object.

        Returns (x, y) coordinates of perimeter, ordred clockwise around
        perimeter.
        '''
        (x, y, xb, yb) = self.do_all_cuts(bit)
        # merge the top and bottom
        xb.reverse()
        yb.reverse()
        x.extend(xb)
        y.extend(yb)
        # close the polygon by adding the first point
        x.append(x[0])
        y.append(y[0])
        return (x, y)

    def triangulate(self, bit):
        '''
        Compute the triangulation of the board.

        bit: A Router_Bit object.

        Returns (x, y, t), where

        x, y = lists of vertex coordinates, ordered clockwise around perimeter
        t = list of triangle indices in x, y

        Note that perimeter() returns a smaller list of (x, y), but more
        coordinates are needed to create a good triangulation.
        '''
        t = []
        y_top = self.yT()
        y_bot = self.yB()
        v = 0
        if self.top_cuts is None:  # has only bottom cuts
            y_cut = y_bot + bit.depth  # y-location of routed edge
            cuts = self.bottom_cuts
            (xc, yc) = self._do_cuts(bit, cuts, y_bot, y_cut)
            nintervals = 2 * len(cuts) - 1
            incut = True
            if cuts[0].xmin > 0:
                nintervals += 1
                incut = False
                xc.insert(0, xc[0])
                yc.insert(0, y_cut)
            if cuts[-1].xmax < self.width:
                nintervals += 1
                xc.append(self.width)
                yc.append(y_cut)
            ntop = nintervals + 1
            ntotal = ntop + len(xc)
            v = [[self.xL(), y_top]] * ntotal
            v[0] = [xc[0], yc[0]]
            v[1] = [xc[1], yc[1]]
            ic = 0
            ibot = 2
            itop = ntotal - 2
            for _ in range(nintervals):
                v[ibot] = [xc[ibot], yc[ibot]]
                if ibot < len(xc) - 1:
                    v[ibot + 1] = [xc[ibot + 1], yc[ibot + 1]]
                if incut:
                    v[itop] = [cuts[ic].xmax + self.xL(), y_top]
                    ic += 1
                    t.append([ibot - 1, ibot, itop])
                    t.append([ibot - 1, itop, itop + 1])
                else:
                    if ic < len(cuts):
                        v[itop] = [cuts[ic].xmin + self.xL(), y_top]
                    else:
                        v[itop] = [self.xR(), y_top]
                    t.append([ibot - 1, ibot, ibot + 1])
                    t.append([ibot - 1, ibot + 1, ibot - 2])
                    t.append([ibot - 2, ibot + 1, itop])
                    t.append([ibot - 2, itop, itop + 1])
                incut = (not incut)
                ibot += 2
                itop -= 1
        elif self.bottom_cuts is None:  # has only top cuts
            y_cut = y_top - bit.depth  # y-location of routed edge
            cuts = self.top_cuts
            (xc, yc) = self._do_cuts(bit, cuts, y_top, y_cut)
            nintervals = 2 * len(cuts) - 1
            incut = True
            if cuts[0].xmin > 0:
                nintervals += 1
                incut = False
                xc.insert(0, xc[0])
                yc.insert(0, y_cut)
            if cuts[-1].xmax < self.width:
                nintervals += 1
                xc.append(self.width)
                yc.append(y_cut)
            nbot = nintervals + 1
            ntotal = nbot + len(xc)
            v = [[self.xL(), y_bot]] * ntotal
            v[0] = [xc[0], yc[0]]
            v[1] = [xc[1], yc[1]]
            ic = 0
            ibot = ntotal - 2
            itop = 2
            for _ in range(nintervals):
                v[itop] = [xc[itop], yc[itop]]
                if itop < len(xc) - 1:
                    v[itop + 1] = [xc[itop + 1], yc[itop + 1]]
                if incut:
                    v[ibot] = [cuts[ic].xmax + self.xL(), y_bot]
                    ic += 1
                    t.append([itop - 1, itop, ibot + 1])
                    t.append([itop, ibot, ibot + 1])
                else:
                    if ic < len(cuts):
                        v[ibot] = [cuts[ic].xmin + self.xL(), y_bot]
                    else:
                        v[ibot] = [self.xR(), y_bot]
                    t.append([itop - 2, itop + 1, itop])
                    t.append([itop - 2, itop, itop - 1])
                    t.append([itop + 1, itop - 2, ibot + 1])
                    t.append([itop + 1, ibot + 1, ibot])
                incut = (not incut)
                itop += 2
                ibot -= 1
        return (v, t)


class Cut(object):
    '''
    Cut description.
    The cut values in Decimals to simplify rounding

    Attributes:

    xmin: min x-location of cut.
    xmax: max x-location of cut.
    passes: Array of router passes to make the cut, indicating the center of the bit
    midPass: The particle pass in passes that is centered (within an increment)
             on the cut
    '''
    def __init__(self, xmin, xmax):
        self.xmin = D(xmin)
        self.xmax = D(xmax)
        self.passes = []
        # Presission value is about 1/64 inch (the exact 1/64 = 0.0156 so we fine for bouth mesument systems)
        self.precision = D('0.01')

    def validate(self, bit, board):
        '''
        Checks whether the attributes of the cut are valid.
        '''
        if self.xmin >= self.xmax:
            raise Router_Exception(bit.transl.tr('cut xmin = %f, xmax = %f: '
                                                 'Must have xmax > xmin!') % (self.xmin, self.xmax))
        if self.xmin < 0:
            raise Router_Exception(bit.transl.tr('cut xmin = %f, xmax = %f: '
                                                 'Must have xmin >=0!') % (self.xmin, self.xmax))
        if self.xmax > board.width:
            raise Router_Exception(bit.transl.tr('cut xmin = %f, xmax = %f:'
                                                 ' Must have xmax < board width (%d)!')
                                   % (self.xmin, self.xmax, board.width))
        if (bit.width_f - (self.xmax - self.xmin)) > self.precision and self.xmin > 0 and self.xmax < board.width:
            raise Router_Exception(bit.transl.tr('cut xmin = %f, xmax = %f ): '
                                                 'Bit width (%f) delta too large for this cut!')
                                   % (self.xmin, self.xmax, bit.width_f))

    def make_router_passes(self, bit, board):
        '''Computes passes for the given bit.
        The logic below assumes bit.width is even for stright bits only
        Here we made board cuts to avoid chips according to the following rules
        1 - avoid full cuts as mach as possible
        2 - expanding cuts shell take about quarter of bit width from left side
        3 - multi-passed corner right cuts
        4 - corner right cut as is (it is most risky cut but we can't optimize it on Incra)
        '''

        self.validate(bit, board)

        cutpass = int((bit.width_f * bit.bit_gentle) / 100)
        halfwidth = bit.width_f / 2

        # alternate between the left and right sides of the overall cut to make the passes
        remainder = self.xmax - self.xmin
        p0 = self.xmax

        if self.xmax == board.width and remainder > halfwidth:
            p0 = self.xmax + halfwidth - cutpass
        else:
            p0 = utils.math_round(self.xmax - halfwidth)  # right size cut

        p1 = utils.math_round(self.xmin + halfwidth)  # left size cut

        self.passes = []

        if self.xmax <= board.width and (self.xmin - (p0 - halfwidth) < self.precision or self.xmin == 0):
            self.passes.append(int(p0))

        while remainder > 0:
            remainder = p0 - p1

            if p0 != p1 and ((p1 + halfwidth) - self.xmax < self.precision or self.xmax == board.width):
                p1 = int(p1)
                self.passes.append(int(p1))

            if remainder <= (bit.width_f * 2) // 3:
                p1 = p0 - remainder // 2
            else:
                p1 += cutpass

            if remainder < (bit.width_f * 4) // 5:
                remainder = 0

        # Sort the passes
        self.passes = sorted(self.passes)
        # Error checking:
        for p in self.passes:
            if (self.xmin > 0 and (self.xmin - (p - halfwidth)) > self.precision) or \
               (self.xmax < board.width and ((p + halfwidth) - self.xmax) > self.precision):
                raise Router_Exception(bit.units.transl.tr('cut xmin = %f, xmax = %f, pass = %f: '
                                                           'Bit width (%f) too large for this cut!')
                                       % (self.xmin, self.xmax, p, bit.width_f))


def adjoining_cuts(cuts, bit, board):
    '''
    Given the cuts on an edge, computes the cuts on the adjoining edge.

    cuts: An array of Cut objects
    bit: A Router_Bit object
    board: A Board object

    Returns an array of Cut objects
    '''

    q_prec =D('0.0001')
    nc = len(cuts)
    offset = bit.width_f-bit.midline
    adjCuts = []

    # if the left-most input cut does not include the left edge, add an
    # adjoining cut that includes the left edge
    if cuts[0].xmin > 0:
        left = 0
        right = cuts[0].xmin + offset - board.dheight
        if right - left >= board.dheight:
            adjCuts.append(Cut(left, right.quantize(q_prec)))

    # loop through the input cuts and form an adjoining cut, formed
    # by looking where the previous cut ended and the current cut starts
    for i in range(1, nc):
        left = cuts[i-1].xmax - offset + board.dheight
        right = cuts[i].xmin + offset - board.dheight
        adjCuts.append(Cut(max(0, left), min(board.width, right)))

    # if the right-most input cut does not include the right edge, add an
    # adjoining cut that includes this edge
    if cuts[-1].xmax < board.width:
        left = cuts[-1].xmax - offset + board.dheight

        right = D(board.width)

        if right - left >= board.dheight:
            adjCuts.append(Cut(max(0, left), min(board.width, right)))

    # print('adjoining_cuts cuts:')
    # dump_cuts(adjCuts)
    return adjCuts


def caul_cuts(cuts, bit, board, trim):
    '''
    Given the cuts on an edge, computes the cuts need to make a caul clamp.

    cuts: An array of Cut objects
    bit: A Router_Bit object
    board: A Board object
    trim: Amount to add to each side of cut (or "trim" from each side of finger)

    Returns an array of Cut objects
    '''
    new_cuts = []
    for c in cuts:
        xmin = max(0, c.xmin - trim)
        xmax = min(board.width, c.xmax + trim)
        cut = Cut(xmin, xmax)
        cut.make_router_passes(bit, board)
        new_cuts.append(cut)
    return new_cuts


def cut_boards(boards, bit, spacing):
    '''
    Determines the cuts for each board for the given bit and spacing
    '''
    # determine all the cuts from the A-cuts (index 0) on the top board.
    last = spacing.cuts
    boards[0].set_bottom_cuts(last, bit)

    if boards[3].active:
        # double-double case
        top = adjoining_cuts(last, bit, boards[0])
        boards[3].set_top_cuts(top, bit)
        last = adjoining_cuts(top, bit, boards[3])
        boards[3].set_bottom_cuts(last, bit)
    if boards[2].active:
        # double and double-double
        top = adjoining_cuts(last, bit, boards[0])
        boards[2].set_top_cuts(top, bit)
        last = adjoining_cuts(top, bit, boards[2])
        boards[2].set_bottom_cuts(last, bit)

    # make the top cuts on the bottom board
    top = adjoining_cuts(last, bit, boards[1])
    boards[1].set_top_cuts(top, bit)


class Joint_Geometry(object):
    '''
    Computes and stores all of the geometry attributes of the joint.
    '''
    def __init__(self, template, boards, bit, spacing, margins, config):
        if config.debug:
            print('construct Joint_Geometry')
        self.template = template
        self.boards = boards
        self.bit = bit
        self.spacing = spacing
        self.margins = margins

        cut_boards(boards, bit, spacing)

        board_sep = margins.sep
        if config.show_fit:
            board_sep = -bit.depth

        # Create the corners of the template
        self.rect_T = My_Rectangle(margins.left, margins.bottom,
                                   template.length, template.height)

        # The sub-rectangle in the template of the board's width
        # (no template margins)
        self.board_T = My_Rectangle(self.rect_T.xL() + template.margin, self.rect_T.yB(),
                                    boards[0].width, template.height)
        x = self.board_T.xL()
        y = self.rect_T.yT() + margins.sep

        # Set bottom board origin
        self.boards[1].set_origin(x, y)
        y = self.boards[1].yT() + board_sep

        # Set double and double-double origins
        if self.boards[2].active:
            self.boards[2].set_origin(x, y)
            y = self.boards[2].yT() + board_sep
            if self.boards[3].active:
                self.boards[3].set_origin(x, y)
                y = self.boards[3].yT() + board_sep

        # Set top board origin
        self.boards[0].set_origin(x, y)
        y = self.boards[0].yT() + margins.sep

        # Template stuff for double-double cases
        if self.boards[3].active:
            self.rect_TDD = My_Rectangle(margins.left, y,
                                         template.length, template.height)
            self.board_TDD = My_Rectangle(self.rect_TDD.xL() + template.margin, y,
                                          boards[0].width, template.height)
            y = self.board_TDD.yT() + margins.sep
        else:
            self.rect_TDD = None
            self.board_TDD = None

        # Caul template
        if config.show_caul:
            caul_trim = max(1, bit.units.abstract_to_increments(config.caul_trim))
            self.rect_caul = My_Rectangle(margins.left, y,
                                          template.length, template.height)
            self.board_caul = My_Rectangle(self.rect_caul.xL() + template.margin, y,
                                           boards[0].width, template.height)
            self.caul_top = caul_cuts(self.boards[0].bottom_cuts, bit, boards[0], caul_trim)
            self.caul_bottom = caul_cuts(self.boards[1].top_cuts, bit, boards[1], caul_trim)
        else:
            self.rect_caul = None
            self.board_caul = None
            self.caul_top = None
            self.caul_bottom = None

        self.compute_fit()

    def compute_fit(self):
        '''
        Sets the maximum gap and overlap over all joints.
        '''
        # The gap is same around allof joints:
        self.max_gap = 0
        self.max_overlap = 0

        if self.bit.gap > 0:
            self.max_gap = self.bit.gap
        else:
            self.max_overlap = -self.bit.gap


def create_title(boards, bit, spacing):
    '''
    Returns a title that describes the joint
    '''
    units = bit.units
    title = spacing.description
    title += units.transl.tr('\nBoard width: ')
    title += units.increments_to_string(boards[0].width, True)
    if boards[2].active:
        title += units.transl.tr('   Double Thickness: ')
        title += units.increments_to_string(boards[2].dheight, True)
        if boards[3].active:
            title += ', '
            title += units.increments_to_string(boards[2].dheight, True)
    title += units.transl.tr('    Bit: ')
    if bit.angle > 0:
        title += units.transl.tr('%.1f\xB0 dovetail') % bit.angle
    else:
        title += units.transl.tr('straight')
    title += units.transl.tr(', width: ')
    title += units.increments_to_string(bit.width, True)
    title += units.transl.tr(', depth: ')
    title += units.increments_to_string(bit.depth, True)

    if units.metric:
        quant = D('0.05') # metric measurment limit
        gap = bit.gap.quantize(units.quant)
    else:
        quant = D(1/64).quantize(units.quant) # english scale measurmentlimit 1/64 more than enough
        gap = D(units.increments_to_inches(bit.gap)).quantize(units.quant)

    if bit.angle > 0 and\
            (abs(gap) > quant or\
             gap > D(spacing.config.warn_gap) or\
             gap < (-1 * D(spacing.config.warn_overlap))):
        title += units.transl.tr('\x7c%s') % gap
        title += units.transl.tr(' (%s)') % units.increments_to_string(bit.depth_0, True)
    return title
