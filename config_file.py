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
This module contains utilities for creating and reading the
user configuration file.
'''

import os, imp
import utils

_CONFIG_INIT = r'''
######################################################################
# Options for pyRouterJig.  Be careful editing this file.  Any errors
# that occur will not be friendly.
#
# This file is a python script.  Here's some basics:
#
# If # is the first character on a line, it's a comment line.
# True and False are logical values (you must capitalize the first letter).
# None is also a value, sometimes used below to indicate "use the default."
#
# Also, [inches|mm] below means "inches or millimeters".  The value is in
# inches (if metric=False) or mm (if metric=True).  The value may be an
# integer, floating point, or fractional value.  Fractional values must
# be in quotes.
#
######################################################################
# Do not change version, because this tells pyRouterJig which
# code version initially created this file.
version = '{version}'
######################################################################
# Options below may be changed
######################################################################

# If True, use metric units.  If False, use English units.
metric = {metric}

# The number of increments per unit length (integer value, or None). 
# All dimensions and router passes are restricted to
#   (unit length) / (num_increments) 
# The unit length is
#   1 inch (metric = False)
#   1 mm   (metric = True)
# For the Incra LS Positioner, use
#    32 (metric = False), corresponding to 1/32" resolution
#    1  (metric = True), corresponding to 1mm resolution
num_increments = {num_increments}

# If true, label each finger with its size.  This option may also be turned
# on and off under the menu "View" and selecting "Finger Sizes".
label_fingers = {label_fingers}

# If true, label each router passes on the board.  This option may also be turned
# on and off under the menu "View" and selecting "Router Passes".
show_router_passes = {show_router_passes}

# Initial board width [inches|mm]
# Example of fractional value. 7.5 is equivalent.
board_width = {board_width}

# Initial bit width [inches|mm]
# Another example of fractional value. 0.5 is equivalent.
bit_width = {bit_width}

# Initial bit depth [inches|mm] 
# Example of floating point. '3/4' is equivalent.
bit_depth = {bit_depth}

# Initial bit angle [degrees]
bit_angle = {bit_angle}

# Initial thickness of double and double-double boards.
double_board_thickness = {double_board_thickness}

# Avoid fingers that are smaller than this dimension [inches|mm]
min_finger_width = {min_finger_width}

# Trim this amount from each side of the Top- and Bottom-board fingers to form
# the optional clamping cauls [inches|mm]
caul_trim = {caul_trim}

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure [inches|mm]
top_margin = {top_margin}
bottom_margin = {bottom_margin}
left_margin = {left_margin}
right_margin = {right_margin}
separation = {separation}

# On save image, minimum width of image in pixels. Used if the figure width is
# less than this size.  Does not apply to screenshots, which are done at the
# resolution of the window.
min_image_width = {min_image_width}

# On save image, maximum width of image in pixels. Used if the figure width is
# less than this size.  Does not apply to screenshots, which are done at the
# resolution of the window.
# Set to min_image_width to force that resolution for every image.
max_image_width = {max_image_width}

# Scaling factor for printing.  Set to 1.0 for no scaling.  If your printed templates
# measure Y inches instead of X inches, set to X / Y. You may use a forumla
# here. Make sure that you use decimal points for numbers (floating point). Example:
# print_scale_factor = 9.5 / (9.5 - 1.0 / 32.0)
print_scale_factor = {print_scale_factor}

# The folder which contains wood grain image files.  Prefix the string with the character-r to prevent
# python from interpreting the character-\ (used in Windows file paths) as an escape.
wood_images = r'{wood_images}'

# This is either a wood name (the file prefix of an image file in wood_images),
# or the following Qt fill patterns:
# DiagCrossPattern, BDiagPattern, FDiagPattern, Dense1Pattern, Dense5Pattern
default_wood = '{default_wood}'

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
debug = {debug}

# Colors are specified as a mix of three values between 0 and 255, as
#     (red, green, blue)
# Examples:
# (255, 0, 0) red
# (0, 255, 0) green
# (0, 0, 255) blue
# (255, 255, 255) white
# (0, 0, 0) black
#
# Useful site: http://www.colorpicker.com/

# Background color
background_color = {background_color}
'''

# common default values
common_vals = {'version':'NONE',
               'label_fingers':True,
               'show_router_passes':True,
               'bit_angle':0,
               'min_image_width':1440,
               'max_image_width':'min_image_width',
               'print_scale_factor':1.0,
               'wood_images':'NONE',
               'default_wood':'DiagCrossPattern',
               'debug':False,
               'left_margin':'top_margin',
               'right_margin':'top_margin',
               'separation':'top_margin',
               'background_color':(240, 231, 201)}

# default values for english units
english_vals = {'metric':False,
                'num_increments':32,
                'board_width':"'7 1/2'",
                'bit_width':"'1/2'",
                'bit_depth':0.75,
                'double_board_thickness':"'1/8'",
                'min_finger_width':"'1/16'",
                'caul_trim':"'1/32'",
                'top_margin':"'1/4'",
                'bottom_margin':"'1/2'"}

# default values for metric units
metric_vals = {'metric':True,
               'num_increments':1,
               'board_width':200,
               'bit_width':12,
               'bit_depth':12,
               'double_board_thickness':4,
               'min_finger_width':2,
               'caul_trim':1,
               'top_margin':6,
               'bottom_margin':12}

def version_number(version):
    '''Splits the string version into its integer version number.  X.Y.Z -> XYZ'''
    vs = version.split('.')
    return int(vs[0]) * 100 + int(vs[1]) * 10 + int(vs[2])

def parameters_to_increments(config, units):
    '''
    Converts parameters in the config file to their appropriate increment values, based on
    units.
    '''
    config.board_width = units.abstract_to_increments(config.board_width)
    config.bit_width = units.abstract_to_increments(config.bit_width)
    config.bit_depth = units.abstract_to_increments(config.bit_depth)
    config.bit_angle = utils.abstract_to_float(config.bit_angle)
    config.min_finger_width = max(1, units.abstract_to_increments(config.min_finger_width))
    config.double_board_thickness = units.abstract_to_increments(config.double_board_thickness)
    config.caul_trim = max(1, units.abstract_to_increments(config.caul_trim))
    config.top_margin = units.abstract_to_increments(config.top_margin)
    config.bottom_margin = units.abstract_to_increments(config.bottom_margin)
    config.left_margin = units.abstract_to_increments(config.left_margin)
    config.right_margin = units.abstract_to_increments(config.right_margin)
    config.separation = units.abstract_to_increments(config.separation)

class Configuration(object):
    '''
    Defines interface to reading and creating the configuration file
    '''
    def __init__(self):
        self.filename = os.path.join(os.path.expanduser('~'), '.pyrouterjig')
        # version number as integer. config file must be updated if it was created
        # with an earlier number
        self.min_version_number = 85
        self.config = None
    def read_config(self):
        '''
        Reads the configuration file.  If it does not exist, it's created.
        '''
        if not os.path.exists(self.filename):
            return 1
        else:
            self.config = imp.load_source('', self.filename)
            vnum = version_number(self.config.version)
            msg_level = 0
            if vnum < self.min_version_number:
                return 2
            else:
                return 0
    def create_config(self, metric):
        '''
        Creates the configuration file.
        '''
        common_vals['wood_images'] = os.path.join(os.path.expanduser('~'), 'wood_images')
        common_vals['version'] = str(utils.VERSION)
        if metric:
            common_vals.update(metric_vals)
        else:
            common_vals.update(english_vals)
        content = _CONFIG_INIT.format(**common_vals)
        fd = open(self.filename, 'w')
        fd.write(content)
        fd.close()
