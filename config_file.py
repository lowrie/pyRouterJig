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
This module contains utilities for creating and reading the
user configuration file.
'''

import os

from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

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

# Thelast saved file name
last_path = r'{last_path}'

######################################################################
# These options may be set through the pyRouterJig:Preferences menu
######################################################################

# If True, use metric units.  If False, use English units.
metric = {metric}

# Application Language
language = r'{language}'

# The number of increments per unit length.
# All dimensions and router passes are restricted to
#   (unit length) / (num_increments) 
# The unit length is
#   1 inch (metric = False)
#   1 mm   (metric = True)
# For the Incra LS Positioner, use
#    32 (metric = False), corresponding to 1/32" resolution
#    1  (metric = True), corresponding to 1mm resolution
num_increments = {num_increments}

# If true, label each finger with its width.  This option may also be turned
# on and off under the menu "View" and selecting "Finger Widths".
show_finger_widths = {show_finger_widths}

# If true, then label each router pass with its identifier on the board.  This
# option may also be turned on and off under the menu "View", selecting
# "Router Passes", and selecting "Identifiers"
show_router_pass_identifiers = {show_router_pass_identifiers}

# If true, then label each router pass with its location on the board.  This
# option may also be turned on and off under the menu "View", selecting
# "Router Passes", and selecting "Locations"
show_router_pass_locations = {show_router_pass_locations}

# If true, then show the caul template.  This option may also be turned on and
# off under the menu "View" and selecting "Caul Template"
show_caul = {show_caul}

# If true, then show the fit of the joint.  This option may also be turned on and
# off under the menu "View" and selecting "Fit"
show_fit = {show_fit}

# Initial board width [inches|mm]
board_width = {board_width}

# Initial bit width [inches|mm]
bit_width = {bit_width}

# Initial bit depth [inches|mm] 
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

# If the gap in the joint exceeds this value, warn the user [inches|mm]
warn_gap = {warn_gap}

# If the overlap in the joint exceeds this value, warn the user [inches|mm]
warn_overlap = {warn_overlap}

# Cutting part of the bit %
bit_gentle = {bit_gentle}

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

# Template line width. 
# Default value 0.3
line_width = {line_width}

# The folder which contains wood grain image files.  Prefix the string with the character-r to prevent
# python from interpreting the character-\ (used in Windows file paths) as an escape.
wood_images = r'{wood_images}'

# This is either a wood name (the file prefix of an image file in wood_images),
# or the following Qt fill patterns:
# DiagCrossPattern, BDiagPattern, FDiagPattern, Dense1Pattern, Dense5Pattern
default_wood = r'{default_wood}'

# Colors are specified as a mix of three values between 0 and 255, as
#     (red, green, blue)
# Examples:
# (255, 0, 0) red
# (0, 255, 0) green
# (0, 0, 255) blue
# (255, 255, 255) white
# (0, 0, 0) black
#
# In addition, you can add an optional alpha value between 0 and 255, where
# 0 is transparent and 255 opaque, as
#     (red, green, blue, alpha)
#
# Useful site: http://www.colorpicker.com/

# Canvas colors
canvas_background = {canvas_background}
canvas_foreground = {canvas_foreground}

# Watermark
watermark_color = {watermark_color}

# Template margin
template_margin_background = {template_margin_background}
template_margin_foreground = {template_margin_foreground}

# The board colors.  Background mainly for the 'Solid Fill' board selection.
board_background = {board_background}
board_foreground = {board_foreground}

# Foreground colors for each pass on the template
pass_color = {pass_color}
pass_alt_color = {pass_alt_color}

# Foreground color the template centerline
center_color = {center_color}

# If true, print color.  Otherwise, colors are converted to black and white when printing.
print_color = {print_color}

######################################################################
# These options may NOT be set through the pyRouterJig:Preferences menu
######################################################################

# For English units, the string separator between the whole and fraction components
english_separator = '{english_separator}'

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure [inches|mm]
top_margin = {top_margin}
bottom_margin = {bottom_margin}
left_margin = {left_margin}
right_margin = {right_margin}
separation = {separation}

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
debug = {debug}
'''

# common default values.  The canvas, board, and template colors from
# http://paletton.com/#uid=50F0u0kllllaFw0g0qFqFg0-obq
COMMON_VALS = {'version': 'NONE',
               'last_path': 'pyrouterjig.png',
               'english_separator': ' ',
               'language': 'en_US',
               'show_finger_widths': False,
               'show_router_pass_identifiers': True,
               'show_router_pass_locations': False,
               'show_caul': False,
               'show_fit': False,
               'bit_gentle': 33.0,
               'bit_angle': 0,
               'min_image_width': 1440,
               'max_image_width': 'min_image_width',
               'line_width': 0.3,
               'print_scale_factor': 1.0,
               'wood_images': 'NONE',
               'default_wood': '1',
               'debug': False,
               'print_color': True,
               'canvas_background': (255, 237, 184, 255),
               'canvas_foreground': (91, 68, 0, 255),
               'watermark_color': (0, 0, 0, 75),
               'template_margin_background': (212, 203, 106, 255),
               'template_margin_foreground': (91, 83, 0, 255),
               'board_background': (212, 167, 106, 255),
               'board_foreground': (91, 52, 0, 255),
               'pass_color': (0, 0, 0, 255),
               'pass_alt_color': (255, 0, 0, 255),
               'center_color': (0, 200, 0, 255)}

# default values for english units
ENGLISH_VALS = {'metric': False,
                'num_increments': 32,
                'board_width': '7 1/2',
                'bit_width': '1/2',
                'bit_depth': 0.75,
                'double_board_thickness': '1/8',
                'min_finger_width': '1/16',
                'caul_trim': '1/32',
                'warn_gap': 0.005,
                'warn_overlap': 0.000,
                'top_margin': '1/4',
                'bottom_margin': '1/2',
                'left_margin': '1/4',
                'right_margin': '1/4',
                'separation': '1/4'}

# default values for metric units
METRIC_VALS = {'metric': True,
               'num_increments': 1,
               'board_width': 200,
               'bit_width': 12,
               'bit_depth': 12,
               'double_board_thickness': 4,
               'min_finger_width': 2,
               'caul_trim': 1,
               'warn_gap': 0.05,
               'warn_overlap': 0.000,
               'top_margin': 6,
               'bottom_margin':12,
               'left_margin': 6,
               'right_margin': 6,
               'separation': 6}


# values that are migrated to new versions of the config file.  Don't include metric, because it's
# always migrated.
MIGRATE = ['english_separator',  # COMMON_VALS
           'language',
           'show_finger_widths',
           'show_router_passes',
           'show_caul',
           'show_fit',
           'bit_angle',
           'min_image_width',
           'max_image_width',
           'print_scale_factor',
           'default_wood',
           'debug',
           'bit_gentle',
           'left_margin',
           'right_margin',
           'separation',
           'background_color',
           'board_fill_colors',
           'num_increments',  # METRIC_VALS or ENGLISH_VALS
           'board_width',
           'bit_width',
           'bit_depth',
           'double_board_thickness',
           'min_finger_width',
           'caul_trim',
           'warn_gap',
           'warn_overlap',
           'top_margin',
           'bottom_margin']

# Values that have either metric or English dimensions
DIM_VALS = ['separation',
            'board_width',
            'bit_angle',
            'bit_width',
            'bit_depth',
            'double_board_thickness',
            'min_finger_width',
            'caul_trim',
            'warn_gap',
            'warn_overlap',
            'top_margin',
            'bottom_margin',
            'left_margin',
            'right_margin']


def version_number(version):
    '''Splits the string version into its integer version number.  X.Y.Z -> XYZ'''
    vs = version.split('.')
    return int(vs[0]) * 100 + int(vs[1]) * 10 + int(vs[2])


def set_default_dimensions(d):
    '''Sets the default dimensional quantites in the config dictionary d'''
    if d['metric']:
        COMMON_VALS.update(METRIC_VALS)
    else:
        COMMON_VALS.update(ENGLISH_VALS)
    d['num_increments'] = COMMON_VALS['num_increments']
    for v in DIM_VALS:
        d[v] = COMMON_VALS[v]


class Configuration(object):
    '''
    Defines interface to reading and creating the configuration file
    '''
    def __init__(self):
        self.filename = os.path.join(os.path.expanduser('~'), '.pyrouterjig')
        # config file must be updated if it was created with an earlier number.
        # Update this value when new parameters are added to the config file,
        # or any parameter's type changes,
        self.create_version_number = 94
        # config file cannot be migrated from versions earlier than this.
        # This value is currently set at the version that all dimensions and bit_angle
        # were consistent types and dimensions.
        self.migrate_version_number = 83
        self.config = None

    def read_config(self):
        '''
        Reads the configuration file.  Return values:
           0: Config file was read successfully
           1: Config file does not exist
           2: Config file was read successfully, but it is outdated
        '''
        if not os.path.exists(self.filename):
            return 1
        dummy_module_dir, module_file = os.path.split(self.filename)
        module_name, dummy_module_ext = os.path.splitext(module_file)

        # Here we call loader directly inorder to avoid extension analyses (tricky!)
        spec = spec_from_loader(module_name, SourceFileLoader(module_name, self.filename))
        self.config = module_from_spec(spec)
        spec.loader.exec_module(self.config)

        try:
            t = int(self.config.default_wood)
            self.config.default_wood = t
        except ValueError:
            pass

        vnum = version_number(self.config.version)
        if vnum < self.create_version_number:
            return 2
        return 0

    def create_config(self, metric):
        '''
        Creates the configuration file.  Return values:
          0: All values default
          1: Values were migrated from old config file
        '''
        COMMON_VALS['wood_images'] = os.path.join(os.path.expanduser('~'), 'wood_images')
        COMMON_VALS['version'] = str(utils.VERSION)
        if metric:
            COMMON_VALS.update(METRIC_VALS)
        else:
            COMMON_VALS.update(ENGLISH_VALS)
        r = 0
        if self.config is not None:
            # Then config file was outdated
            vnum = version_number(self.config.version)
            if vnum >= self.migrate_version_number:
                # Then we can migrate the old settings
                r = 1
                for m in MIGRATE:
                    if m in self.config.__dict__.keys():
                        COMMON_VALS[m] = self.config.__dict__[m]
        self.write_config(COMMON_VALS)
        return r

    def write_config(self, vals):
        '''
        Writes the configuration file using the dictionary vals.
        '''
        w = vals.copy()
        for i in DIM_VALS:
            if isinstance(w[i], str):
                w[i] = "'{}'".format(w[i])
        content = _CONFIG_INIT.format(**w)
        fd = open(self.filename, 'w')
        fd.write(content)
        fd.close()
