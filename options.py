
'''
Options for pyRouterJig.  Be careful editing this file.  Any errors
that occur will not be friendly.  Also, these options may change
or be deleted with future versions.
'''
# Do not change these 2 lines ##########################################
from utils import Margins
OPTIONS = {}

# You can change the options below.

# Dots-per-inch for the screen (integer value)
OPTIONS['dpi_screen'] = 110

# Dots-per-inch for printing (integer value)
OPTIONS['dpi_paper'] = 72

# min_finger_width: avoid fingers that are smaller than this dimension.
# Specified in intervals (integer).  So for English units, 8 corresponds to
# 4/32" = 1/8"
OPTIONS['min_finger_width'] = 4

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure.  Specified in intervals (integer).
# Here we just set all margins to 1/4".
OPTIONS['margins'] = Margins(8, bottom=16)

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
OPTIONS['debug'] = False
#OPTIONS['debug'] = True

