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

from copy import deepcopy
import matplotlib.pyplot as plt
from options import OPTIONS
import router

class MPL_Plotter(object):
    '''
    Plots the template and boards using matplotlib.
    '''
    def __init__(self, title=None):
        self.title = title
        self.fig = plt.figure(dpi=OPTIONS['dpi_screen'])
        self.fig_width = 10.0
        self.fig_height = 3.5
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

        axes, margins = self.create_axes(template, board)

        # Generate the new geometry layout
        geom = router.Joint_Geometry(template, board, bit, spacing, margins)

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
            for p in range(len(c.passes) - 1, -1, -1):
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
            for p in range(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dA' % ip
                axes.plot([xp, xp], [rect_T.yMid(), rect_T.yT()], color="black",
                          linewidth=1.0, linestyle="-")
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    axes.annotate(s=label, xy=(xp, rect_T.yT()), xytext=(0, -2),
                                  textcoords='offset points', rotation='vertical',
                                  ha='right', va='top', fontsize=self.pass_fontsize)

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
        axes.plot((board_T.xMid(), board_T.xMid()), (rect_T.yB, board_A.yT()), color="black",
                  linewidth=1.0, linestyle='--')

        # Add a title
        title = self.title
        if title is None:
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
        axes.annotate(title, (board_T.xMid(), 0), va='bottom', ha='center',
                      textcoords='offset points', xytext=(0, 2))

        # get rid of all plotting margins and axes
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        #####plt.axis('off')
        # ... this is also needed so that PDFs get rid of the margins
        axes.xaxis.set_major_locator(plt.NullLocator())
        axes.yaxis.set_major_locator(plt.NullLocator())

        self.fig.canvas.draw()
    def create_axes(self, template, board):
        '''
        Resets the figure size and creates the axes
        '''
        # Try default options, but reset if the template is too small for margins
        margins = deepcopy(OPTIONS['margins'])

        # Set the window limits
        window_width = template.length + margins.left + margins.right
        window_height = template.height + 2 * (board.height + margins.sep) + \
                        margins.bottom + margins.top

        min_width = 10
        wwl = OPTIONS['units'].intervals_to_inches(window_width)
        if wwl < min_width:
            wwl = min_width
            window_width = OPTIONS['units'].inches_to_intervals(wwl)
            margins.left = (window_width - template.length) / 2
            margins.right = margins.left
            window_width = template.length + margins.left + margins.right
        wwh = OPTIONS['units'].intervals_to_inches(window_height)

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
            if OPTIONS['debug']:
                print 'doing blank draw'
            self.fig.canvas.draw() # only do this on board resize

        # Adjust to the new figure size
        if OPTIONS['debug']:
            print 'mpl fig size ', self.fig_width, self.fig_height
        self.fig.set_size_inches(self.fig_width, self.fig_height)
        axes = self.fig.add_subplot(1, 1, 1, aspect='equal')

        # Set the window limits in frac dimensions
        axes.set_xlim([0, window_width])
        axes.set_ylim([0, window_height])

        return axes, margins
    def savefig(self, filename):
        '''
        Saves the figure to filename
        '''
        self.fig.savefig(filename, dpi=OPTIONS['dpi_paper'],
                         bbox_inches='tight', pad_inches=0)
