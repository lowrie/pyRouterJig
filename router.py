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
Contains the router, board, template and their geometry properties.
'''
from __future__ import division
from __future__ import print_function
from future.utils import lrange

import math
import copy
from utils import my_round

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

    angle: measured from y-axis, in degrees, following dovetail bit
           standard. Zero for straight bit.

    width: max cutting width.  This is the bottom of a dovetail bit.
           For now, this must be an even number.

    depth: cutting depth. Equals board thickness for through dovetails
            and box joints.

    Computed attributes:

    offset: x-dimension between max-width point and point at board's
            surface.  Zero for angle=0.

    neck: width of bit at board surface.

    halfwidth: half of width
    '''
    def __init__(self, units, width, depth, angle=0):
        self.units = units
        self.width = width
        self.depth = depth
        self.angle = angle
        self.reinit()
    def set_width_from_string(self, s):
        '''
        Sets the width from the string s, following requirements from units.string_to_increments().
        '''
        msg = 'Bit width is %s\n' % s
        if self.units.metric:
            msg += 'Set to an even positive integer value, such as 6'
        else:
            msg += 'Set to a positive value, such as 1/2'
        try:
            self.width = self.units.string_to_increments(s)
        except ValueError as e:
            msg = 'ValueError setting bit width: %s\n\n' % (e) + msg
            raise Router_Exception(msg)
        except:
            raise
        if self.width <= 0:
            raise Router_Exception(msg)
        self.halfwidth = self.width // 2
        if 2 * self.halfwidth != self.width:
            pmsg = 'Bit width must be an even number of increments.\n'
            if not self.units.metric:
                pmsg += 'The increment size is 1/%d"\n\n' % self.units.increments_per_inch
            raise Router_Exception(pmsg + msg)
        self.reinit()
    def set_depth_from_string(self, s):
        '''
        Sets the depth from the string s, following requirements from units.string_to_increments().
        '''
        msg = 'Bit depth is %s\n' % s
        if self.units.metric:
            msg += 'Set to a positive integer value, such as 5'
        else:
            msg += 'Set to a positive value, such as 3/4'
        try:
            self.depth = self.units.string_to_increments(s)
        except ValueError as e:
            msg = 'ValueError setting bit depth: %s\n\n' % (e) + msg
            raise Router_Exception(msg)
        except:
            raise
        if self.depth <= 0:
            raise Router_Exception(msg)
        self.reinit()
    def set_angle_from_string(self, s):
        '''
        Sets the angle from the string s, where s represents a floating point number.
        '''
        msg = 'Bit angle is %s\nSet to zero or a positive floating-point value, such as 7.5' % s
        try:
            self.angle = float(s)
        except ValueError as e:
            msg = 'ValueError setting bit angle: %s\n\n' % (e) + msg
            raise Router_Exception(msg)
        except:
            raise
        if self.angle < 0:
            raise Router_Exception(msg)
        self.reinit()
    def reinit(self):
        '''
        Reinitializes internal attributes that are dependent on width
        and angle.
        '''
        self.halfwidth = self.width // 2
        self.offset = 0 # ensure exactly 0 for angle == 0
        if self.angle > 0:
            self.offset = self.depth * math.tan(self.angle * math.pi / 180)
        self.neck = self.width - 2 * self.offset
    def scale(self, s):
        '''Scales dimensions by the factor s'''
        self.width = my_round(self.width * s)
        self.width += self.width % 2 # ensure even
        self.depth = my_round(self.depth * s)
        self.reinit()
    def change_units(self, new_units):
        '''Changes units to new_units'''
        s = self.units.get_scaling(new_units)
        if s == 1:
            return
        self.width = my_round(self.width * s)
        self.width += self.width % 2 # ensure even
        self.depth = my_round(self.depth * s)
        self.units = new_units
        self.reinit()

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
    def set_wood(self, wood):
        self.wood = wood
    def set_active(self, active=True):
        self.active = active
    def set_width_from_string(self, s):
        '''
        Sets the width from the string s, following requirements from units.string_to_increments().
        '''
        msg = 'Board width is %s\n' % s
        if self.units.metric:
            msg += 'Set to a postive integer value, such as 52'
        else:
            msg += 'Set to a postive value, such as 7 1/2'
        try:
            self.width = self.units.string_to_increments(s)
        except ValueError as e:
            msg = 'ValueError setting board width: %s\n\n' % (e) + msg
            raise Router_Exception(msg)
        except:
            raise
        if self.width <= 0:
            raise Router_Exception(msg)
    def set_height(self, bit, dheight=None):
        '''
        Sets the height from the router bit depth of cut
        '''
        if dheight is None:
            if self.dheight > 0:
                h = self.dheight
            else:
                h = my_round(0.5 * bit.depth)
        else:
            self.dheight = dheight
            h = dheight
        self.height = bit.depth + h
    def set_height_from_string(self, bit, s):
        '''
        Sets the height from the string s, following requirements from units.string_to_increments().
        This sets the attribute dheight, which is the increment above the bit depth.
        '''
        msg = 'Board height increment is %s\n' % s
        if self.units.metric:
            msg += 'Set to a postive integer value, such as 5'
        else:
            msg += 'Set to a postive value, such as 1/2'
        try:
            t = self.units.string_to_increments(s)
        except ValueError as e:
            msg = 'ValueError setting board thickness increment: %s\n\n' % (e) + msg
            raise Router_Exception(msg)
        except:
            raise
        if t <= 0:
            raise Router_Exception(msg)
        self.set_height(bit, t)
    def change_units(self, new_units):
        '''Changes units to new_units'''
        s = self.units.get_scaling(new_units)
        if s == 1:
            return
        self.width = my_round(self.width * s)
        self.height = my_round(self.height * s)
        self.thickness = my_round(self.thickness * s)
        self.units = new_units
    def set_bottom_cuts(self, cuts, bit):
        for c in cuts:
            c.make_router_passes(bit, self)
        self.bottom_cuts = cuts
    def set_top_cuts(self, cuts, bit):
        for c in cuts:
            c.make_router_passes(bit, self)
        self.top_cuts = cuts
    def _do_cuts(self, bit, cuts, y_nocut, y_cut):
        x = [self.xL()]
        if cuts[0].xmin > 0:
            y = [y_nocut]
        else:
            y = [y_cut]
        # loop through the cuts and add them to the perimeter
        for c in cuts:
            if c.xmin > 0:
                # on the surface, start of cut
                x.append(c.xmin + x[0] + bit.offset)
                y.append(y_nocut)
            # at the cut depth, start of cut
            x.append(c.xmin + x[0])
            y.append(y_cut)
            # at the cut depth, end of cut
            x.append(c.xmax + x[0])
            y.append(y_cut)
            if c.xmax < self.width:
                # at the surface, end of cut
                x.append(c.xmax + x[0] - bit.offset)
                y.append(y_nocut)
        # add the last point on the top and bottom, at the right edge,
        # accounting for whether the last cut includes this edge or not.
        if cuts[-1].xmax < self.width:
            x.append(x[0] + self.width)
            y.append(y_nocut)
        return (x, y)
    def perimeter(self, bit):
        '''
        Compute the perimeter coordinates of the board.

        bit: A Router_Bit object.
        '''
        # Do the top edge
        y_nocut = self.yT() # y-location of uncut edge
        if self.top_cuts is None:
            x = [self.xL(), self.xR()]
            y = [y_nocut, y_nocut]
        else:
            y_cut = y_nocut - bit.depth   # y-location of routed edge
            (x, y) = self._do_cuts(bit, self.top_cuts, y_nocut, y_cut)
        # Do the bottom edge
        y_nocut = self.yB() # y-location of uncut edge
        if self.bottom_cuts is None:
            xb = [self.xL(), self.xR()]
            yb = [y_nocut, y_nocut]
        else:
            y_cut = y_nocut + bit.depth   # y-location of routed edge
            (xb, yb) = self._do_cuts(bit, self.bottom_cuts, y_nocut, y_cut)
        # merge the top and bottom
        xb.reverse()
        yb.reverse()
        x.extend(xb)
        y.extend(yb)
        # close the polygon by adding the first point
        x.append(x[0])
        y.append(y[0])
        return (x, y)

class Cut(object):
    '''
    Cut description.

    Attributes:

    xmin: min x-location of cut.
    xmax: max x-location of cut.
    passes: Array of router passes to make the cut, indicating the center of the bit
    midPass: The particle pass in passes that is centered (within an increment)
             on the cut
    '''
    def __init__(self, xmin, xmax):
        self.xmin = xmin
        self.xmax = xmax
        self.passes = []
    def validate(self, bit, board):
        '''
        Checks whether the attributes of the cut are valid.
        '''
        if self.xmin >= self.xmax:
            raise Router_Exception('cut xmin = %d, xmax = %d: '\
                                   'Must have xmax > xmin!' % (self.xmin, self.xmax))
        if self.xmin < 0:
            raise Router_Exception('cut xmin = %d, xmax = %d: '\
                                   'Must have xmin >=0!' % (self.xmin, self.xmax))
        if self.xmax > board.width:
            raise Router_Exception('cut xmin = %d, xmax = %d:'
                                   ' Must have xmax < board width (%d)!'\
                                   % (self.xmin, self.xmax, board.width))
        if self.xmax - self.xmin < bit.width and self.xmin > 0 and self.xmax < board.width:
            raise Router_Exception('cut xmin = %d, xmax = %d: '\
                                   'Bit width (%d) too large for this cut!'\
                                   % (self.xmin, self.xmax, bit.width))
    def make_router_passes(self, bit, board):
        '''Computes passes for the given bit.'''
        # The logic below assumes bit.width is even
        if bit.width % 2 != 0:
            Router_Exception('Router-bit width must be even!')
        self.validate(bit, board)
        # set current extents of the uncut region
        xL = self.xmin
        xR = self.xmax
        # alternate between the left and right sides of the overall cut to make the passes
        remainder = xR - xL
        self.passes = []
        while remainder > 0:
            # start with a pass on the right side of cut
            p = xR - bit.halfwidth
            if p - bit.halfwidth >= self.xmin or self.xmin == 0:
                self.passes.append(p)
                xR -= bit.width
            # if anything to cut remains, do a pass on the far left side
            remainder = xR - xL
            if remainder > 0:
                p = xL + bit.halfwidth
                if p + bit.halfwidth <= self.xmax or self.xmax == board.width:
                    self.passes.append(p)
                    xL += bit.width
                    remainder = xR - xL
                    # at this stage, we've done the same number of left and right passes, so if
                    # there's only one more pass needed, center it.
                    if remainder > 0 and remainder <= bit.width:
                        p = (xL + xR) // 2
                        self.passes.append(p)
                        remainder = 0
        # Sort the passes
        self.passes = sorted(self.passes)
        # Error checking:
        for p in self.passes:
            if (self.xmin > 0 and p - bit.halfwidth < self.xmin) or \
               (self.xmax < board.width and p + bit.halfwidth > self.xmax):
                raise Router_Exception('cut xmin = %d, xmax = %d, pass = %d: '\
                                       'Bit width (%d) too large for this cut!'\
                                       % (self.xmin, self.xmax, p, bit.width))

def adjoining_cuts(cuts, bit, board):
    '''
    Given the cuts on an edge, computes the cuts on the adjoining edge.

    cuts: An array of Cut objects

    Returns an array of Cut objects
    '''
    nc = len(cuts)
    adjCuts = []
    # if the left-most input cut does not include the left edge, add an
    # adjoining cut that includes the left edge
    if cuts[0].xmin > 0:
        left = 0
        right = my_round(cuts[0].xmin + bit.offset) - board.dheight
        if right - left >= board.dheight:
            adjCuts.append(Cut(left, right))
    # loop through the input cuts and form an adjoining cut, formed
    # by looking where the previous cut ended and the current cut starts
    for i in lrange(1, nc):
        left = my_round(cuts[i-1].xmax - bit.offset + board.dheight)
        right = max(left + bit.width, my_round(cuts[i].xmin + bit.offset) - board.dheight)
        adjCuts.append(Cut(left, right))
    # if the right-most input cut does not include the right edge, add an
    # adjoining cut that includes this edge
    if cuts[-1].xmax < board.width:
        left = my_round(cuts[-1].xmax - bit.offset) + board.dheight
        right = board.width
        if right - left >= board.dheight:
            adjCuts.append(Cut(left, right))
    return adjCuts

class Joint_Geometry(object):
    '''
    Computes and stores all of the geometry attributes of the joint.
    '''
    def __init__(self, template, boards, bit, spacing, margins):
        self.template = template
        self.boards = boards
        self.bit = bit
        self.spacing = spacing

        # determine all the cuts from the a-cuts (index 0)
        last = spacing.cuts
        self.boards[0].set_bottom_cuts(last, bit)
        if self.boards[3].active:
            # double-double case
            top = adjoining_cuts(last, bit, boards[0])
            self.boards[3].set_top_cuts(top, bit)
            last = adjoining_cuts(top, bit, boards[3])
            self.boards[3].set_bottom_cuts(last, bit)
        if self.boards[2].active:
            # double and double-double
            top = adjoining_cuts(last, bit, boards[0])
            self.boards[2].set_top_cuts(top, bit)
            last = adjoining_cuts(top, bit, boards[2])
            self.boards[2].set_bottom_cuts(last, bit)
        
        # make the top cuts on the bottom board
        top = adjoining_cuts(last, bit, boards[1])
        self.boards[1].set_top_cuts(top, bit)

        # Create the corners of the template
        self.rect_T = My_Rectangle(margins.left, margins.bottom,
                                   template.length, template.height)

        # The sub-rectangle in the template of the board's width
        # (no template margins)
        self.board_T = My_Rectangle(self.rect_T.xL() + template.margin, self.rect_T.yB(), \
                                    boards[0].width, template.height)
        x = self.board_T.xL()
        y = self.rect_T.yT() + margins.sep

        # Set bottom board origin
        self.boards[1].set_origin(x, y)
        y = self.boards[1].yT() + margins.sep

        # Set double and double-double origins
        if self.boards[2].active:
            self.boards[2].set_origin(x, y)
            y = self.boards[2].yT() + margins.sep
            if self.boards[3].active:
                self.boards[3].set_origin(x, y)
                y = self.boards[3].yT() + margins.sep

        # Set top board origin
        self.boards[0].set_origin(x, y)
        y = self.boards[0].yT() + margins.sep

        # Template stuff for double-double cases
        self.rect_TDD = My_Rectangle(margins.left, y,
                                     template.length, template.height)
        self.board_TDD = My_Rectangle(self.rect_TDD.xL() + template.margin, y, \
                                      boards[0].width, template.height)
