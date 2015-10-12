##########################################################################
#
# Options for pyRouterJig.  Be careful editing this file.  Any errors
# that occur will not be friendly.  Also, these options may change
# or be deleted with future versions.
#
# Do not change these 2 lines ############################################
from utils import Units, Margins
class Options: pass # Empty class.  Static attributes added below.
##########################################################################

# You can change the options below.

# units sets the unit system and size of an interval.
# Use this line for English, with a 1/32" interval size:
Options.units = Units(intervals_per_inch=32)
# Use this line for metric, which always uses a 1mm interval size:
#Options.units = Units(metric=True)

# Dots-per-inch for the screen (integer value)
Options.dpi_screen = 110

# Dots-per-inch for printing (integer value)
Options.dpi_paper = 72

# min_finger_width: avoid fingers that are smaller than this dimension.
# Specified in intervals (integer).  So for English units, 8 corresponds to
# 8/32" = 1/4"
Options.min_finger_width = 8

# The margins object controls top, bottom, and side margins, along with the
# separation between objects in the figure.  Specified in intervals (integer).
# Here we just set all margins to 1/4".
Options.margins = Margins(8)

# Set debug to True to turn on debugging.  This will print a lot of output to
# stdout during a pyRouterJig session.  This option is typically only useful
# for developers.
Options.debug = False

# If True, use the Qt menubar attached to the application. Otherwise, use the
# native menubar for the platform.
Options.use_qt_menubar = False

