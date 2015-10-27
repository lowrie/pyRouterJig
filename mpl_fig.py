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
Contains the matplotlib functionality for drawing the template and boards.
'''
from __future__ import print_function
from __future__ import division
from future.utils import lrange

from copy import deepcopy
import matplotlib.pyplot as plt
from options import OPTIONS
import router

from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)

class MPL_QtFig(object):
    '''
    Interface to the qt_driver, using matplotlib to draw the boards and template.
    '''
    def __init__(self, template, board):
        self.dpi = OPTIONS['dpi_paper']
        self._mpl = MPL_Plotter(template, board)
        self.canvas = FigureCanvas(self._mpl.fig)
    def draw(self, template, board, bit, spacing):
        '''
        Draws the template and boards
        '''
        self._mpl.draw(template, board, bit, spacing)
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

class MPL_Plotter(object):
    '''
    Plots the template and boards using matplotlib.
    This class should be universal for any GUI driver.
    '''
    def __init__(self, template, board):
        self.fig = plt.figure(dpi=OPTIONS['dpi_screen'])
        self.fig_width = -1
        self.fig_height = -1
        self.set_fig_dimensions(template, board)
        self.fig.set_size_inches(self.fig_width, self.fig_height)
        # if subsequent passes are less than this value, don't label the pass (in intervals)
        self.sep_annotate = 4
        # fontsize for pass labels.  If this value is increased, likely need to increase
        # sep_annotate.
        self.pass_fontsize = 9
    def draw(self, template, board, bit, spacing):
        '''
        Draws the entire figure
        '''
        # Generate the new geometry layout and draw the template
        axes = self.create_axes(template, board)
        geom = router.Joint_Geometry(template, board, bit, spacing, self.margins)
        self.draw_template(axes, geom)

        # Plot the boards
        board_A = geom.board_A
        board_B = geom.board_B
        axes.fill(geom.xB, geom.yB, hatch='/', fill=None)
        axes.fill(geom.xA, geom.yA, hatch='/', fill=None)
        axes.annotate('Board-A', (board_A.xMid(), board_A.yT()), va='top', ha='center',
                      textcoords='offset points', xytext=(0, -3))
        axes.annotate('Board-B', (board_B.xMid(), board_B.yB), va='bottom', ha='center',
                      textcoords='offset points', xytext=(0, 3))

        # Plot the board center
        axes.plot((geom.board_T.xMid(), geom.board_T.xMid()), (geom.rect_T.yB, board_A.yT()),
                  color="black", linewidth=1.0, linestyle='--')

        # Add a title
        title = spacing.description
        title += '    Board width: '
        title += OPTIONS['units'].intervals_to_string(board.width, True)
        title += '    Bit: '
        if bit.angle > 0:
            title += '%.1f deg. dovetail' % bit.angle
        else:
            title += 'straight'
        title += ', width: '
        title += OPTIONS['units'].intervals_to_string(bit.width, True)
        title += ', depth: '
        title += OPTIONS['units'].intervals_to_string(bit.depth, True)
        axes.annotate(title, (geom.board_T.xMid(), 0), va='bottom', ha='center',
                      textcoords='offset points', xytext=(0, 2))

        # get rid of all plotting margins and axes
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        # ... this is also needed so that PDFs get rid of the margins
        axes.xaxis.set_major_locator(plt.NullLocator())
        axes.yaxis.set_major_locator(plt.NullLocator())

        self.fig.canvas.draw()
    def set_fig_dimensions(self, template, board):
        '''
        Computes the figure dimension attributes, fig_width and fig_height, in inches.
        Returns True if the dimensions changed.
        '''
        # Try default margins, but reset if the template is too small for margins
        self.margins = deepcopy(OPTIONS['margins'])

        # Set the window limits
        self.window_width = template.length + self.margins.left + self.margins.right
        self.window_height = template.height + 2 * (board.height + self.margins.sep) + \
                             self.margins.bottom + self.margins.top

        min_width = 10
        wwl = OPTIONS['units'].intervals_to_inches(self.window_width)
        if wwl < min_width:
            wwl = min_width
            self.window_width = OPTIONS['units'].inches_to_intervals(wwl)
            self.margins.left = (self.window_width - template.length) // 2
            self.margins.right = self.margins.left
            self.window_width = template.length + self.margins.left + self.margins.right
        wwh = OPTIONS['units'].intervals_to_inches(self.window_height)

        dimensions_changed = False
        if wwl != self.fig_width:
            self.fig_width = wwl
            dimensions_changed = True
        if wwh != self.fig_height:
            self.fig_height = wwh
            dimensions_changed = True

        return dimensions_changed
    def create_axes(self, template, board):
        '''
        Resets the figure size and creates the axes
        '''
        # Draw a blank screen only if the figure dimensions change. Without
        # this logic, get a flickering effect on each re-draw.
        do_blank_draw = self.set_fig_dimensions(template, board)

        # Clear out any previous figure
        self.fig.clear()
        if do_blank_draw:
            if OPTIONS['debug']:
                print('doing blank draw')
            self.fig.canvas.draw() # only do this on board resize

        # Adjust to the new figure size
        if OPTIONS['debug']:
            print('mpl fig size ', self.fig_width, self.fig_height)
        self.fig.set_size_inches(self.fig_width, self.fig_height)
        axes = self.fig.add_subplot(1, 1, 1, aspect='equal')

        # Set the window limits in frac dimensions
        axes.set_xlim([0, self.window_width])
        axes.set_ylim([0, self.window_height])

        return axes
    def draw_template(self, axes, geom):
        '''
        Draws the Incra template
        '''

        # Plot the template bounding box
        rect_T = geom.rect_T
        axes.plot(rect_T.xAll(), rect_T.yAll(), color="black",
                  linewidth=1.0, linestyle="-")

        # Fill the template margins with a grayshade
        board_T = geom.board_T
        axes.fill_betweenx([rect_T.yB, rect_T.yT()], [rect_T.xL, rect_T.xL],
                           [board_T.xL, board_T.xL], facecolor='0.9', linewidth=0)
        axes.fill_betweenx([rect_T.yB, rect_T.yT()], [board_T.xR(), board_T.xR()],
                           [rect_T.xR(), rect_T.xR()], facecolor='0.9', linewidth=0)

        # Plot the router passes
        # ... do the B passes
        ip = 0
        for c in geom.bCuts[::-1]:
            for p in lrange(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dB' % ip
                axes.plot([xp, xp], [rect_T.yB, rect_T.yMid()], color="black",
                          linewidth=1.0, linestyle="-")
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    axes.annotate(s=label, xy=(xp, rect_T.yB), xytext=(0, 2),
                                  textcoords='offset points', rotation='vertical',
                                  ha='right', va='bottom', fontsize=self.pass_fontsize)
        # ... do the A passes
        ip = 0
        for c in geom.aCuts[::-1]:
            for p in lrange(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dA' % ip
                axes.plot([xp, xp], [rect_T.yMid(), rect_T.yT()], color="black",
                          linewidth=1.0, linestyle="-")
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    axes.annotate(s=label, xy=(xp, rect_T.yT()), xytext=(0, -2),
                                  textcoords='offset points', rotation='vertical',
                                  ha='right', va='top', fontsize=self.pass_fontsize)
    def savefig(self, filename):
        '''
        Saves the figure to filename
        '''
        self.fig.savefig(filename, dpi=OPTIONS['dpi_paper'],
                         bbox_inches='tight', pad_inches=0)
