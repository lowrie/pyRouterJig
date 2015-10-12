###########################################################################
#
# Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)
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

from copy import deepcopy
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib import widgets
from options import Options
import utils
import router

class MPL_Plotter:
    '''
    Plots the template and boards using matplotlib.
    '''
    def __init__(self, title=None):
        self.title = title
        self.fig = plt.figure(dpi=Options.dpi_screen)
        self.fig_width = 10.0
        self.fig_height = 3.5
        self.fig.set_size_inches(self.fig_width, self.fig_height)
        # if subsequent passes are less than this value, don't label the pass (in intervals)
        self.sep_annotate = 4
        # fontsize for pass labels.  If this value is increased, likely need to increase
        # sep_annotate.
        self.pass_fontsize = 9
    def draw(self, template, board, bit, spacing):
        self.template = template
        self.board = board
        self.bit = bit
        self.spacing = spacing

        # Try default options, but reset if the template is too small for margins
        margins = deepcopy(Options.margins)

        # Set the window limits
        window_width  = self.template.length + margins.left + margins.right
        window_height = self.template.height + 2 * (self.board.height + margins.sep) + \
                        margins.bottom + margins.top

        min_width = 10
        wwl = Options.units.intervals_to_inches(window_width)
        if wwl < min_width:
            wwl = min_width
            window_width = Options.units.inches_to_intervals(wwl)
            margins.left = (window_width - self.template.length) / 2
            margins.right = margins.left
            window_width  = self.template.length + margins.left + margins.right
        wwh = Options.units.intervals_to_inches(window_height)
        
        # Set the final figure width and height, and determine whether to draw
        # a blank screen to erase the old figure.  Draw a blank screen only if
        # the figure dimensions change. Without this logic, get a flickering
        # effect on each re-draw.
        do_blank_draw = False
        if wwl != self.fig_width:
            self.fig_width = wwl
            do_blank_draw = True
        if wwh != self.fig_height:
            self.fig_height = wwh
            do_blank_draw = True

        # Clear out any previous figure
        self.fig.clear()
        if do_blank_draw: 
            if Options.debug: print 'doing blank draw'
            self.fig.canvas.draw() # only do this on board resize

        # Adjust to the new figure size
        if Options.debug: print 'mpl fig size ', self.fig_width, self.fig_height
        self.fig.set_size_inches(self.fig_width, self.fig_height)
        self.axes = self.fig.add_subplot(1,1,1, aspect='equal')

        # Set the window limits in frac dimensions
        self.axes.set_xlim([0, window_width])
        self.axes.set_ylim([0, window_height])

        # Generate the new geometry layout
        self.geom = router.Joint_Geometry(self.template, self.board, self.bit, self.spacing, margins)

        # Plot the template bounding box
        rect_T = self.geom.rect_T
        self.axes.plot(rect_T.xAll(), rect_T.yAll(), color="black", \
                       linewidth=1.0, linestyle="-")

        # Fill the template margins with a grayshade
        board_T = self.geom.board_T
        self.axes.fill_betweenx([rect_T.yB, rect_T.yT()], [rect_T.xL, rect_T.xL], \
                                [board_T.xL, board_T.xL], facecolor='0.9', linewidth=0)
        self.axes.fill_betweenx([rect_T.yB, rect_T.yT()], [board_T.xR(), board_T.xR()], \
                                [rect_T.xR(), rect_T.xR()], facecolor='0.9', linewidth=0)

        # Plot the router passes
        # ... do the B passes
        ip = 0
        for c in self.geom.bCuts[::-1]:
            for p in range(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dB' % ip
                self.axes.plot([xp,xp], [rect_T.yB, rect_T.yMid()], color="black", \
                               linewidth=1.0, linestyle="-")
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    self.axes.annotate(s=label, xy=(xp, rect_T.yB), xytext=(0,2), \
                                       textcoords='offset points', rotation='vertical', \
                                       ha='right', va='bottom', fontsize=self.pass_fontsize)
        # ... do the A passes
        ip = 0
        for c in self.geom.aCuts[::-1]:
            for p in range(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dA' % ip
                self.axes.plot([xp,xp], [rect_T.yMid(), rect_T.yT()], color="black", \
                               linewidth=1.0, linestyle="-")
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    self.axes.annotate(s=label, xy=(xp, rect_T.yT()), xytext=(0,-2), \
                                       textcoords='offset points', rotation='vertical', \
                                       ha='right', va='top', fontsize=self.pass_fontsize)

        # Plot the boards
        board_A = self.geom.board_A
        board_B = self.geom.board_B
        self.axes.fill(self.geom.xB, self.geom.yB, hatch='/', fill=None)
        self.axes.fill(self.geom.xA, self.geom.yA, hatch='/', fill=None)
        self.axes.annotate('Board-A', (board_A.xMid(), board_A.yT()), va='top', ha='center', \
                           textcoords='offset points', xytext=(0,-3))
        self.axes.annotate('Board-B', (board_B.xMid(), board_B.yB), va='bottom', ha='center', \
                           textcoords='offset points', xytext=(0,3))

        # Plot the board center
        self.axes.plot((board_T.xMid(), board_T.xMid()), (rect_T.yB, board_A.yT()), color="black",
                       linewidth=1.0, linestyle='--')

        # Add a title
        title = self.title
        if title is None:
            title = self.spacing.description
            title += '    Board width: '
            title += Options.units.intervals_to_string(self.board.width, True)
            title += '    Bit: '
            if self.bit.angle > 0:
                title += '%.1f deg. dovetail' % self.bit.angle
            else:
                title += 'straight'
            title += ', width: '
            title += Options.units.intervals_to_string(self.bit.width, True)
            title += ', depth: '
            title += Options.units.intervals_to_string(self.bit.depth, True)
        self.axes.annotate(title, (board_T.xMid(), 0), va='bottom', ha='center',
                           textcoords='offset points', xytext=(0,2))

        # get rid of all plotting margins and axes
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1,wspace=0, hspace=0)
        #####plt.axis('off')
        # ... this is also needed so that PDFs get rid of the margins
        self.axes.xaxis.set_major_locator(plt.NullLocator())
        self.axes.yaxis.set_major_locator(plt.NullLocator())

        self.fig.canvas.draw()
    def savefig(self, filename):
        self.fig.savefig(filename, dpi=Options.dpi_paper, bbox_inches='tight', pad_inches=0)
