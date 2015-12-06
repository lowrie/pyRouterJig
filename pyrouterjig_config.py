######################################################################
# Options for pyRouterJig.  Be careful editing this file.  Any errors
# that occur will not be friendly.
#
# This file is a python script.
######################################################################

import os

# If true, use metric units.  If False, use English units.
metric = False

# If using English units, this parameter sets the size of an increment.
# Ignored for metric units, where 1 increment = 1 mm.
increments_per_inch = 32

# Starting board width, in increments
board_width = 240

# Starting bit width, in increments
bit_width = 16

# Starting bit depth, in increments
bit_depth = 24

# Starting bit angle, in degrees
bit_angle = 0

# Avoid fingers that are smaller than this dimension.
# Specified in increments.
min_finger_width = 2

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure.
# Specified in increments.
top_margin = 8
left_margin = top_margin
right_margin = top_margin
bottom_margin = 16

# Define the wood types used to color the boards.
# This list is used to build the Wood menu.
wood_dir = os.path.os.path.join(os.path.expanduser('~'), 'woods')
woods = {'Cherry':'black-cherry-sealed.png',\
         'Maple':'hard-maple.png',\
         'Walnut':'black-walnut-sealed.png'}
default_wood = 'Cherry'

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
# debug = False
debug = True

