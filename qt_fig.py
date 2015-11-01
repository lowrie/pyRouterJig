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
Contains the Qt functionality for drawing the template and boards.
'''
from __future__ import print_function
from __future__ import division
from future.utils import lrange

from copy import deepcopy
from options import OPTIONS
import router
from utils import my_round

from PyQt4 import QtGui
from PyQt4 import QtCore
#from PySide import QtCore, QtGui

class Qt_Fig(object):
    '''
    Interface to the qt_driver, using Qt to draw the boards and template.
    '''
    def __init__(self, template, board):
        self.dpi = OPTIONS['dpi_paper']
        self.canvas = Qt_Plotter(template, board)
    def draw(self, template, board, bit, spacing):
        '''
        Draws the template and boards
        '''
        self.canvas.draw(template, board, bit, spacing)
    def get_save_file_types(self):
        '''
        Returns a string of supported file choices for use with QFileDialog()
        and the default.
        '''
        default = 'Portable Network Graphics (*.png)'
        file_choices = QtGui.QImageWriter.supportedImageFormats()
        print(file_choices)

        return (file_choices, default)
    def save(self, path):
        '''
        Saves figure to path
        '''
        self.canvas.print_figure(path, dpi=self.dpi)

class Qt_Plotter(QtGui.QWidget):
    '''
    Plots the template and boards using Qt.
    '''
    def __init__(self, template, board):
        QtGui.QWidget.__init__(self)
        self.dpi = OPTIONS['dpi_screen']
        self.fig_width = -1
        self.fig_height = -1
        self.set_fig_dimensions(template, board)
        # if subsequent passes are less than this value, don't label the pass (in intervals)
        self.sep_annotate = 4
        # fontsize for pass labels.  If this value is increased, likely need to increase
        # sep_annotate.
        self.pass_fontsize = 9
        self.geom = None
    def minimumSizeHint(self):
        return QtCore.QSize(100, 100)
    def sizeHint(self):
        return QtCore.QSize(self.window_width, self.window_height)
    def set_fig_dimensions(self, template, board):
        '''
        Computes the figure dimension attributes, fig_width and fig_height, in 
        intervals.
        Returns True if the dimensions changed.
        '''
        # Try default margins, but reset if the template is too small for margins
        self.margins = deepcopy(OPTIONS['margins'])

        # Set the figure dimensions
        fig_width = template.length + self.margins.left + self.margins.right
        fig_height = template.height + 2 * (board.height + self.margins.sep) + \
                     self.margins.bottom + self.margins.top

        min_width = 320
        if fig_width < min_width:
            fig_width = min_width
            self.margins.left = (fig_width - template.length) // 2
            self.margins.right = self.margins.left
            fig_width = template.length + self.margins.left + self.margins.right

        dimensions_changed = False
        if fig_width != self.fig_width:
            self.fig_width = fig_width
            dimensions_changed = True
        if fig_height != self.fig_height:
            self.fig_height = fig_height
            dimensions_changed = True

        scale = self.dpi * board.units.intervals_to_inches(1)
        self.window_width = int(scale * fig_width)
        self.window_height = int(scale * fig_height)

        return dimensions_changed
    def draw(self, template, board, bit, spacing):
        '''
        Draws the entire figure
        '''
        # Generate the new geometry layout
        self.set_fig_dimensions(template, board)
        self.geom = router.Joint_Geometry(template, board, bit, spacing, self.margins)
        self.update()
    def savefig(self, filename):
        '''
        Saves the figure to filename
        '''
        self.fig.savefig(filename, dpi=OPTIONS['dpi_paper'],
                         bbox_inches='tight', pad_inches=0)
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        if self.geom is None:
            painter.drawRect(10, 10, 40, 30)
            return

        size = self.size()
        self.window_width = size.width()
        self.window_height = size.height()

        painter.fillRect(0, 0, self.window_width, self.window_height, \
                         QtGui.QBrush(QtGui.QColor(255, 234, 163)))
                         

        window_ar = float(self.window_width) / self.window_height
        fig_ar = float(self.fig_width) / self.fig_height

        # transform the painter to maintain the figure aspect ratio in the current 
        # window
        if fig_ar < window_ar:
            w = my_round(fig_ar * self.window_height)
            painter.translate((self.window_width - w) // 2, self.window_height)
            s = float(self.window_height) / self.fig_height
        else:
            h = my_round(self.window_width / fig_ar)
            painter.translate(0, (self.window_height + h) // 2)
            s = float(self.window_width) / self.fig_width
        painter.scale(s, -s)

        painter.setPen(QtCore.Qt.black)
        
        # draw the objects
        self.draw_template(painter)
        self.draw_boards(painter)
        self.draw_title(painter)

        painter.end()
    def paint_text(self, painter, text, coord, flags, shift=(0,0), angle=0, fill=None):
        '''
        Puts text at coord with alignment flags.
        '''
        transform = painter.transform()
        (x, y) = transform.map(coord[0], coord[1])
        x += shift[0]
        y += shift[1]
        painter.resetTransform()
        painter.translate(x, y)
        painter.rotate(angle)
        big = 5000
        xorg = 0
        yorg = 0
        if flags & QtCore.Qt.AlignRight:
            xorg = -big
        elif flags & QtCore.Qt.AlignHCenter:
            xorg = -big // 2
        if flags & QtCore.Qt.AlignBottom:
            yorg = -big
        rect = QtCore.QRect(xorg, yorg, big, big)
        rect = painter.boundingRect(rect, flags, text)
        if fill is not None:
            painter.fillRect(rect, fill)
        painter.drawText(rect, flags, text)
        painter.setTransform(transform)
    def draw_template(self, painter):
        '''
        Draws the Incra template
        '''
        rect_T = self.geom.rect_T
        board_T = self.geom.board_T

        # Fill the entire template as white
        painter.fillRect(rect_T.xL, rect_T.yB, rect_T.width, rect_T.height, QtCore.Qt.white)

        # Fill the template margins with a grayshade
        brush = QtGui.QBrush(QtGui.QColor(220, 220, 220))
        painter.fillRect(rect_T.xL, rect_T.yB, board_T.xL - rect_T.xL, 
                         rect_T.height, brush)
        painter.fillRect(board_T.xR(), rect_T.yB, rect_T.xR() - board_T.xR(), 
                         rect_T.height, brush)

        # Draw the template bounding box
        painter.drawRect(rect_T.xL, rect_T.yB, rect_T.width, rect_T.height)

        # Draw the router passes
        # ... do the B passes
        ip = 0
        flags = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        shift = (0, -2)
        for c in self.geom.bCuts[::-1]:
            for p in lrange(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dB' % ip
                painter.drawLine(xp, rect_T.yB, xp, rect_T.yMid())
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    self.paint_text(painter, label, (xp, rect_T.yB), flags, shift, -90)
       # ... do the A passes
        ip = 0
        flags = QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom
        shift = (0, 2)
        for c in self.geom.aCuts[::-1]:
            for p in lrange(len(c.passes) - 1, -1, -1):
                xp = c.passes[p] + board_T.xL
                ip += 1
                label = '%dA' % ip
                painter.drawLine(xp, rect_T.yMid(), xp, rect_T.yT())
                if p == 0 or c.passes[p] - c.passes[p-1] > self.sep_annotate:
                    self.paint_text(painter, label, (xp, rect_T.yT()), flags, shift, -90)
    def draw_one_board(self, painter, x, y):
        '''
        Draws a single board
        '''
        painter.save()
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(0)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(QtGui.QPixmap('woods/black-cherry-sealed.jpg')))
        n = len(x)
        poly = QtGui.QPolygon()
        for i in lrange(n):
            poly.append(QtCore.QPoint(x[i], y[i]))
        painter.drawPolygon(poly)
        painter.restore()
    def draw_boards(self, painter):
        '''
        Draws all the boards
        '''
        self.draw_one_board(painter, self.geom.xA, self.geom.yA)
        self.draw_one_board(painter, self.geom.xB, self.geom.yB)

        fill = QtGui.QBrush(QtGui.QColor(255, 234, 163))

        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        p = (self.geom.board_A.xMid(), self.geom.board_A.yT())
        self.paint_text(painter, 'A', p, flags, (0, 3), fill=fill)

        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        p = (self.geom.board_B.xMid(), self.geom.board_B.yB)
        self.paint_text(painter, 'B', p, flags, (0, -3), fill=fill)
    def draw_title(self, painter):
        '''
        Draws the title
        '''
        units = self.geom.board.units
        title = self.geom.spacing.description
        title += '\nBoard width: '
        title += units.intervals_to_string(self.geom.board.width, True)
        title += '    Bit: '
        if self.geom.bit.angle > 0:
            title += '%.1f deg. dovetail' % self.geom.bit.angle
        else:
            title += 'straight'
        title += ', width: '
        title += units.intervals_to_string(self.geom.bit.width, True)
        title += ', depth: '
        title += units.intervals_to_string(self.geom.bit.depth, True)
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        p = (self.geom.board_T.xMid(), 0)
        self.paint_text(painter, title, p, flags, (0, -3))
