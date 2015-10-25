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
Creates the Canvas widget for pyQt, containing the object for
matplotlib, mpl.MPL_Plotter
'''
from __future__ import print_function

import mpl
from options import OPTIONS

from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)

class MPL_QtCanvas(object):
    '''
    Qt canvas for MPL_Plotter
    '''
    def __init__(self):
        self.mpl = mpl.MPL_Plotter()
        self.dpi = OPTIONS['dpi_paper']
        self.canvas = FigureCanvas(self.mpl.fig)
    def draw(self, template, board, bit, spacing):
        '''
        Draws the template and boards
        '''
        self.mpl.draw(template, board, bit, spacing)
        self.canvas.draw()
        self.canvas.update()
    def get_save_file_types(self):
        '''
        Returns a string of supported file choices for use with QFileDialog()
        and the default.
        '''
        default = 'Portable Network Graphics (*.png)'
        filetypes = self.canvas.get_supported_filetypes_grouped()
        default_filetype = self.canvas.get_default_filetype()
        file_choices = ''
        for key, value in filetypes.items():
            if len(file_choices) > 0:
                file_choices += ';;'
            # we probably need to consider all value, but for now, just
            # grab the first
            s = key + ' (*.' + value[0] + ')'
            file_choices += s
            if default_filetype == value[0]:
                default = s

        return (file_choices, default)
    def save(self, path):
        '''
        Saves figure to path
        '''
        self.canvas.print_figure(path, dpi=self.dpi)
