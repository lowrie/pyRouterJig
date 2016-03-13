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

VERSION = '0.8.7'

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
    def __init__(self, english_separator, whole=0, numerator=0, denominator=None):
        self.whole = whole
        self.numerator = numerator
        self.denominator = denominator
        self.english_separator = english_separator
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
                s += self.english_separator
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
            # Convert the english_separator to a space
            if self.english_separator != ' ':
                s = s.replace(self.english_separator, ' ', 1)
            # Look for a divisor
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

    english_separator: For English units, string english_separator between whole and fraction
    metric: If true, then use metric (mm).  Otherwise, english (inches)
    num_increments: Number of increments per unit length (1 inch for english, 1 mm for metric)

    Attributes:
    increments_per_inch: Number of increments per inch.
    '''
    mm_per_inch = 25.4
    def __init__(self, english_separator, metric=False, num_increments=None):
        self.english_separator = english_separator
        self.metric = metric
        if num_increments is None:
            if metric:
                self.num_increments = 1
            else:
                self.num_increments = 32
        else:
            self.num_increments = num_increments
        if metric:
            self.increments_per_inch = self.mm_per_inch * self.num_increments
        else: # english units
            self.increments_per_inch = self.num_increments
    def increments_to_inches(self, increments_):
        '''Converts increments to inches.'''
        return float(increments_) / self.increments_per_inch
    def inches_to_increments(self, inches_):
        '''Converts the input inches to increments'''
        return my_round(self.increments_per_inch * inches_)
    def increments_to_string(self, increments, with_units=False):
        '''A string representation of the value increments'''
        if self.metric:
            r = '%g' % (increments / float(self.num_increments))
        else:
            whole = increments // self.increments_per_inch
            numer = increments - self.increments_per_inch * whole
            denom = self.increments_per_inch
            frac = My_Fraction(self.english_separator, whole, numer, denom)
            frac.reduce()
            if frac.numerator > 0 and frac.denominator not in [1, 2, 4, 8, 16, 32, 64]:
                r = '%.3f' % (increments / float(self.num_increments))
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
    def length_to_increments(self, v):
        '''
        Converts v to increments, where v is [inches|mm]
        '''
        return my_round(v * self.num_increments)
    def string_to_float(self, s):
        '''
        Converts a string representation to a floating-point value, where
        the string may contain a fractional value.
        '''
        f = My_Fraction(self.english_separator)
        f.set_from_string(s)
        r = f.whole
        if f.numerator > 0:
            r += float(f.numerator) / f.denominator
        return r
    def abstract_to_float(self, a):
        '''
        Converts a value to a float.  If a is a string, then
        string_to_float() is called.  Otherwise, float() is called.
        '''
        if isinstance(a, str):
            return self.string_to_float(a)
        else:
            return float(a)
    def string_to_increments(self, s):
        '''
        Converts a string representation to the number of increments.
        Assumes the string is in inches or mm, depending on the metric
        attribute.
        '''
        return self.length_to_increments(self.string_to_float(s))
    def abstract_to_increments(self, a):
        '''
        Converts a value to increments.  If a is a string, then
        string_to_increments() is called.  Otherwise, length_to_increments()
        is called.
        '''
        if isinstance(a, str):
            return self.string_to_increments(a)
        else:
            return self.length_to_increments(float(a))
    def valid_number(self, a):
        '''
        Returns true if a represents a valid number, either a string that can
        be converted to a number, or a number itself.
        '''
        try:
            i = self.abstract_to_increments(a)
            if i > 0:
                return True
            else:
                return False
        except:
            return False

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

def print_table(filename, boards, title):
    '''
    Prints a table of router pass locations, referenced to the right size of the board.
    '''
    # Load up the cuts and labels to be printed
    all_cuts = [boards[0].bottom_cuts]
    label_cuts = ['A']
    labels = ['B', 'C', 'D', 'E', 'F']
    i = 0
    if boards[3].active:
        all_cuts.append(boards[3].top_cuts)
        label_cuts.append(labels[i])
        all_cuts.append(boards[3].bottom_cuts)
        label_cuts.append(labels[i + 1])
        i += 2
    if boards[2].active:
        all_cuts.append(boards[2].top_cuts)
        label_cuts.append(labels[i])
        all_cuts.append(boards[2].bottom_cuts)
        label_cuts.append(labels[i + 1])
        i += 2
    all_cuts.append(boards[1].top_cuts)
    label_cuts.append(labels[i])
    # TODO: add cauls
    # Format for each pass, location pair
    form = ' %4s %9s '
    # Print the header
    line = ''
    for k in label_cuts:
        s = 'Pass'
        line += form % (s, 'Location')
    lenh = len(line)
    divider = '-' * lenh + '\n'
    line = divider + line + '\n' + divider
    fd = open(filename, 'w')
    fd.write(title + '\n')
    fd.write(line)
    # Initialize for the print loop
    ncol = len(all_cuts)
    width = boards[0].width
    units = boards[0].units
    pass_index = [0] * ncol
    cut_index = [0] * ncol
    for icol in lrange(ncol):
        cut_index[icol] = len(all_cuts[icol]) - 1
    total_passes = [0] * ncol
    # Print until all of the edges are out of passes.  We go through the cuts,
    # and each pass in the cut, in reverse order (from right to left).
    printing = True
    while printing:
        line = ''
        printing = False
        # Loop through the edges
        for icol in lrange(ncol):
            label = '**'
            dim = '**'
            # check if there are any more passes for this edge
            icut = cut_index[icol]
            if icut >= 0:
                # Still have a pass, so load it
                c = all_cuts[icol][icut]
                np = len(c.passes)
                pi = pass_index[icol]
                total_passes[icol] += 1
                label = '%d%s' % (total_passes[icol], label_cuts[icol])
                dim = units.increments_to_string(width - c.passes[np - pi - 1])
                pass_index[icol] += 1
                printing = True
                # if we are done with this cut, go on to the next cut
                if pass_index[icol] == np:
                    cut_index[icol] -= 1
                    pass_index[icol] = 0
            line += form % (label, dim)
        if printing:
            fd.write(line + '\n')
    fd.close()
