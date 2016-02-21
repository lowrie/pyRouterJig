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
This module contains base utilities for pyRouterJig
'''
from __future__ import division

import math, fractions, os, glob

VERSION = '0.8.1'

def my_round(f):
    '''
    Rounds to the nearest integer
    '''
    return int(round(f))

class My_Fraction(object):
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
        if self.denominator is None or self.numerator == 0:
            return
        dwhole = self.numerator // self.denominator
        self.whole += dwhole
        self.numerator -= dwhole * self.denominator
        gcd = fractions.gcd(self.numerator, self.denominator)
        self.numerator /= gcd
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
                whole_num = sp[0].split(None)
                if len(whole_num) == 1:
                    self.numerator = int(whole_num[0])
                elif len(whole_num) == 2:
                    self.whole = int(whole_num[0])
                    self.numerator = int(whole_num[1])
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

class Units(object):
    '''
    Converts to and from increments and the units being used.

    metric: If true, then use metric (mm).  Otherwise, english (inches)
    align_incra: If true, align for the incra fence.

    Attributes:
    increments_per_inch: Number of increments per inch.
    increments_per_length: Number of increments per unit length (1 inch for english, 1 mm for metric)
    '''
    mm_per_inch = 25.4
    def __init__(self, metric=False, align_incra=True):
        self.metric = metric
        self.align_incra = align_incra
        if align_incra:
            if metric:
                self.increments_per_length = 1
            else:
                self.increments_per_length = 32
        else:
            # Set a very fine alignment
            if metric:
                # 0.01 mm for metric
                self.increments_per_length = 100
            else:
                # Roughly 0.001" for english
                self.increments_per_length = 1024
        if metric:
            self.increments_per_inch = self.mm_per_inch * self.increments_per_length
        else: # english units
            self.increments_per_inch = self.increments_per_length
    def get_scaling(self, new_units):
        '''
        Returns the scaling factor to change the current units to new_units.
        The scaling factor is a floating point number, unless there is no
        change in units or resolution, in which case the integer 1 is returned.
        '''
        s = 1
        if self.metric == new_units.metric:
            if self.increments_per_length != new_units.increments_per_length:
                s = float(new_units.increments_per_length) / self.increments_per_length
        else:
            s = new_units.increments_per_inch / self.increments_per_inch
        return s
    def increments_to_inches(self, increments_):
        '''Converts increments to inches.'''
        return float(increments_) / self.increments_per_inch
    def inches_to_increments(self, inches_):
        '''Converts the input inches to increments'''
        return my_round(self.increments_per_inch * inches_)
    def increments_to_string(self, increments, with_units=False):
        '''A string representation of the value increments'''
        if self.metric:
            r = '%g' % (increments / float(self.increments_per_length))
        else:
            whole = increments // self.increments_per_inch
            numer = increments - self.increments_per_inch * whole
            denom = self.increments_per_inch
            frac = My_Fraction(whole, numer, denom)
            frac.reduce()
            if frac.numerator > 0 and frac.denominator not in [1, 2, 4, 8, 16, 32, 64]:
                r = '%.3f' % (increments / float(self.increments_per_length))
            else:
                r = frac.to_string()
        if with_units:
            r += self.units_string()
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
    def string_to_length(self, s):
        '''
        Converts a string representation to a floating-point length (mm or inch).
        Assumes the string is in inches or mm, depending on the metric
        attribute.
        '''
        if self.metric:
            return float(s)
        f = My_Fraction()
        f.set_from_string(s)
        r = f.whole
        if f.numerator > 0:
            r += float(f.numerator) / f.denominator
        return r
    def length_to_increments(self, v):
        return my_round(v * self.increments_per_length)
    def string_to_increments(self, s):
        '''
        Converts a string representation to the number of increments.
        Assumes the string is in inches or mm, depending on the metric
        attribute.
        '''
        return self.length_to_increments(self.string_to_length(s))
    def abstract_to_increments(self, a):
        if isinstance(a, str):
            return self.string_to_increments(a)
        else:
            return self.length_to_increments(float(a))

class Margins(object):
    '''
    Defines window margins and vertical separation between objects for
    the figure.

    Attributes (all distances in increments)

    sep: Vertical separation between template and Board-B and Board-B
         and Board-A.
    left: Left margin
    right: Right margin
    botoom: Bottom margin
    top: Top margin
    '''
    def __init__(self, default, sep=None, left=None, right=None, bottom=None,
                 top=None):
        '''
        If any value is left unspecified, it's value is set to sep.
        '''
        if sep is None:
            self.sep = default
        else:
            self.sep = default
        if left is None:
            self.left = default
        else:
            self.left = left
        if right is None:
            self.right = default
        else:
            self.right = right
        if bottom is None:
            self.bottom = default
        else:
            self.bottom = bottom
        if top is None:
            self.top = default
        else:
            self.top = top

def create_wood_dict(wood_images):
    '''
    Creates a dictionary {wood_name : wood_image_filename} by parsing the
    directory wood_images.  The wood_name is formed by taking the prefix of the
    wood_image_filename.
    '''
    d = {}
    if not os.path.isdir(wood_images):
        return d
    globber = os.path.join(wood_images, '*')
    files = glob.glob(globber)
    for f in files:
        name = os.path.basename(f)
        i = name.rfind('.')
        if i > 0:
            name = name[0:i]
        path = os.path.abspath(f)
        d[name] = path
    return d

def get_file_index(path, prefix, postfix):
    '''
    Finds the next index available for files that match the signature

      path/prefixINDEXpostfix

    where INDEX is largest integer found, plus 1.  If no files are found, zero is returned.
    '''
    index = -1
    globber = os.path.join(path, prefix + '*' + postfix)
    files = glob.glob(globber)
    npre = len(prefix)
    npost = len(postfix)
    for f in files:
        name = os.path.basename(f)
        name = name[:-npost]
        i = int(name[npre:])
        if i > index:
            index = i
    index += 1
    return index

def set_slider_tick_interval(slider):
    '''
    Sets the QSlider tick interval to a reasonable value
    '''
    minval = slider.minimum()
    maxval = slider.maximum()
    maxtics = 30
    diff = maxval - minval
    if diff > maxtics:
        slider.setTickInterval(diff // maxtics)
    else:
        slider.setTickInterval(1)
