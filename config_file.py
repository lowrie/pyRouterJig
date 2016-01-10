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
user configuration file
'''

import os, imp, shutil
import utils

_CONFIG_INIT = r'''
######################################################################
# Options for pyRouterJig.  Be careful editing this file.  Any errors
# that occur will not be friendly.
#
# This file is a python script, so for example, '#' as the first
# character on a line is a comment.
######################################################################
# Do not change the version, because this tells pyRouterJig which
# version initially created this file.
version = '%s'
######################################################################
# Options below may be changed
######################################################################

# If True, use metric units.  If False, use English units.
metric = False

# If using English units, this parameter sets the size of an increment.
# Ignored for metric units, where 1 increment = 1 mm.
increments_per_inch = 32

# Initial board width, in increments
board_width = 240

# Initial bit width, in increments
bit_width = 16

# Initial bit depth, in increments
bit_depth = 24

# Initial bit angle, in degrees
bit_angle = 0

# Avoid fingers that are smaller than this dimension.
# Specified in increments.
min_finger_width = 2

# Trim this amount from each side of the Top- and Bottom-board fingers to form the optional clamping cauls.
# Specified in increments.
caul_trim = 1

# On save image, minimum width of image in pixels. Used if the figure width is
# less than this size.  Does not apply to screenshots, which are done at the
# resolution of the window.
min_image_width = 1440

# On save image, maximum width of image in pixels. Used if the figure width is
# less than this size.  Does not apply to screenshots, which are done at the
# resolution of the window.
# Set to min_image_width to force that resolution for every image.
max_image_width = min_image_width

# Scaling factor for printing.  Set to 1.0 for no scaling.  If your printed templates
# measure Y inches instead of X inches, set to X / Y. You may use a forumla
# here. Make sure that you use decimal points for numbers (floating point). Example:
# print_scale_factor = 9.5 / (9.5 - 1.0 / 32.0)
print_scale_factor = 1.0

# The folder which contains wood grain image files.  Prefix the string with the character-r to prevent
# python from interpreting the character-\ (used in Windows file paths) as an escape.
wood_images = r'%s'

# This is either a wood name (the file prefix of an image file in wood_images),
# or the following Qt fill patterns:
# DiagCrossPattern, BDiagPattern, FDiagPattern, Dense1Pattern, Dense5Pattern
default_wood = 'DiagCrossPattern'

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
debug = False
#debug = True

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure.
# Specified in increments.
top_margin = 8
left_margin = top_margin
right_margin = top_margin
bottom_margin = 16
separation = top_margin

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
background_color = (240, 231, 201)
'''

def version_number(version):
    '''Splits the string version into its version number'''
    vs = version.split('.')
    return int(vs[0]) * 100 + int(vs[1]) * 10 + int(vs[2])

def create_config(filename):
    '''
    Creates the configuration file.
    '''
    wood_images = os.path.join(os.path.expanduser('~'), 'wood_images')
    content = _CONFIG_INIT % (utils.VERSION, wood_images)
    fd = open(filename, 'w')
    fd.write(content)
    fd.close()

def read_config(min_version_number):
    '''
    Reads the configuration file.  If it does not exist, it's created.
    '''
    global _CONFIG_INIT
    filename = os.path.join(os.path.expanduser('~'), '.pyrouterjig')

    if not os.path.exists(filename):
        # create the config file
        create_config(filename)
        msg = 'Configuration file %s created' % filename
    else:
        msg = 'Read configuration file %s' % filename

    config = imp.load_source('', filename)
    vnum = version_number(config.version)
    msg_level = 0
    if vnum < min_version_number:
        msg_level = 1
        backup = filename + config.version
        shutil.move(filename, backup)
        create_config(filename)
        config = imp.load_source('', filename)
        msg = 'Your configuration file %s was outdated and has been moved to %s.'\
              ' A new configuration file has been created.  Any changes you made'\
              ' to the old file will need to be migrated to the new file.'\
              ' Unfortunately, we are unable to automatically migrate your old'\
              ' settings.' % (filename, backup)

    return (config, msg, msg_level)
