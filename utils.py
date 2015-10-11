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

import math, fractions

version = '0.1.0'

def my_round(f):
    '''
    Rounds to the nearest integer
    '''
    return int(round(f))

class My_Fraction:
    '''
    Represents a number as whole + numerator / denominator, all of which must be 
    integers.

    We call this My_Fraction, to avoid confusion with fractions.Fraction.
    Major differences between My_Fraction and fractions.Fraction:
    - You cannot do arithmetic with My_Fraction
    - My_Fraction includes a whole number attribute.  The equivalent is
      fractions.Fraction(whole * denominator + numerator, denominator)
    '''
    def __init__(self, whole=0, numerator=0, denominator=None):
        self.whole = whole
        self.numerator = numerator
        self.denominator = denominator
    def reduce(self):
        '''
        Reduces the fraction to the minimum values for the numerator and
        denominator.
        '''
        if self.denominator is None or self.numerator == 0: return
        dwhole = self.numerator / self.denominator
        self.whole += dwhole
        self.numerator -= dwhole * self.denominator
        gcd = fractions.gcd(self.numerator, self.denominator)
        self.numerator   /= gcd
        self.denominator /= gcd
    def to_string(self):
        '''
        Converts the fraction to a string representation.
        '''
        self.reduce()
        s = ''
        if self.whole > 0:
            s = '%d' % self.whole
            if self.numerator > 0:
                s += ' '
        if self.numerator > 0:
            s += '%d/%d' % (self.numerator, self.denominator)
        elif self.whole == 0:
            s = '0'
        return s
    def set_from_string(self, s):
        '''
        Initialize from a string assumed to be of the form:

        [whitespace][integer][whitespace][integer][whitespace]/[whitespace][integer][whitespace]
        
        where each of the [] are optional.
        '''
        msg = 'Bad number specification: %s'
        self.whole = 0
        self.numerator = 0
        self.denominator = 1
        dotloc = s.find('.')
        if dotloc == -1:
            # No decimal point, so try fractional form
            sp = s.split('/')
            if len(sp) == 2: # found a divisor
                wholeNum = sp[0].split(None)
                if len(wholeNum) == 1:
                    self.numerator = int(wholeNum[0])
                elif len(wholeNum) == 2:
                    self.whole = int(wholeNum[0])
                    self.numerator = int(wholeNum[1])
                else:
                    raise ValueError(msg % s)
                denom = sp[1].split(None)
                if len(denom) == 1:
                    self.denominator = int(denom[0])
                else:
                    raise ValueError(msg % s)
            elif len(sp) == 1: # no divisor, so must be a whole number
                self.whole = int(sp[0])
            else:
                raise ValueError(msg % s)
        else:
            # found a decimal point
            whole = s[:dotloc].strip()
            if len(whole) > 0:
                self.whole = int(whole)
            rest = s[dotloc+1:].strip()
            if len(rest) > 0:
                self.numerator = int(rest)
                self.denominator = my_round(math.pow(10, int(math.log10(self.numerator))+1))
                self.reduce()

class Units:
    '''
    Converts to and from intervals and the units being used.

    metric: If true, then an interval corresponds to 1 mm.
    
    intervals_per_inch:  For metric false, this correpsonds 
    to the number of intervals per inch.  So a value of 32
    (the default) corresponds an interval size of 1/32".
    For metric true, this values is the number of mm in an inch.

    '''
    def __init__(self, intervals_per_inch=32, metric=False):
        self.metric = metric
        self.intervals_per_inch = intervals_per_inch
        if metric:
            self.intervals_per_inch = 25.4
    def intervals_to_inches(self, intervals_):
        '''Converts intervals to inches.'''
        return float(intervals_) / self.intervals_per_inch
    def inches_to_intervals(self, inches_):
        '''Converts the input inches to intervals'''
        return my_round(self.intervals_per_inch * inches_)
    def intervals_to_string(self, intervals, with_units=False):
        '''A string representation of the value intervals'''
        if self.metric:
            return '%d' % intervals
        whole = int(intervals / self.intervals_per_inch)
        numer = intervals - self.intervals_per_inch * whole
        denom = self.intervals_per_inch
        r = My_Fraction(whole, numer, denom).to_string()
        if with_units: r += self.units_string()
        return r
    def units_string(self, verbose=False):
        '''Returns a string that represents the units'''
        if self.metric:
            if verbose:
                return ' millimeters'
            else:
                return ' mm'
        else:
            if verbose:
                return ' inches'
            else:
                return '"'
    def string_to_intervals(self, s):
        '''
        Converts a string representation to the number of intervals.
        Assumes the string is in inches or mm, depending on the metric
        attribute.
        '''
        if self.metric:
            return int(s)
        f = My_Fraction()
        f.set_from_string(s)
        r = f.whole * self.intervals_per_inch
        if f.numerator > 0:
            ratio = self.intervals_per_inch / f.denominator
            if ratio * f.denominator != self.intervals_per_inch:
                raise ValueError('"%s" is not an exact number of intervals' % s)
            r += ratio * f.numerator
        return r

class Margins:
    '''
    Defines window margins and vertical separation between objects
    '''
    def __init__(self, sep, left=None, right=None, bottom=None, top=None):
        self.sep = sep
        if left is None:
            self.left = sep
        else:
            self.left = left
        if right is None:
            self.right = sep
        else:
            self.right = right
        if bottom is None:
            self.bottom = sep
        else:
            self.bottom = bottom
        if top is None:
            self.top = sep
        else:
            self.top = top

class Options:
    '''
    Stores global the options:

    debug: If true, prints extra diagnostics for developers.
    use_qt_menubar: If True, use the Qt menubar attached to the
      application. Otherwise, use the native menubar for the
      platform.
    units: The global Units object.
    margins: The global Margins object.
    dpi_screen: Dots-per-inch used for screen plotting.
    dpi_paper: Dots-per-inch used for screen printing.
    min_finger_width: avoid a finger smaller than dimension
    '''
    def __init__(self):
        self.debug = False
        self.use_qt_menubar = False
        self.units = Units(32)
        self.margins = Margins(self.units.inches_to_intervals(0.25))
        self.dpi_screen = 110
        self.dpi_paper = 72
        self.min_finger_width = self.units.inches_to_intervals(0.125)

options = Options()

# Some helper functions for the global Options object:
def inches_to_intervals(inches):
    return options.units.inches_to_intervals(inches)
def string_to_intervals(s):
    return options.units.string_to_intervals(s)
def intervals_to_string(i, with_units=False):
    return options.units.intervals_to_string(i, with_units)
def intervals_to_inches(i):
    return options.units.intervals_to_inches(i)
