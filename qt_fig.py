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

import copy
from options import OPTIONS
import router
from utils import my_round

import pyRouterJig_rc

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui

def paint_text(painter, text, coord, flags, shift=(0, 0), angle=0, fill=None):
    '''
    Puts text at coord with alignment flags.

    painter: QPainter object
    text: The text to print.
    coord: The coordinate at which to place the text
    flags: QtCore.Qt alignment flags
    shift: Adjustments in coord, in pixels
    angle: Rotation angle
    fill: If not None, a QBrush that fills the bounding rectangle behind the text.
    '''
    # Save the current transform, then switch to transform that places the origin
    # at coord and rotated by angle.
    transform = painter.transform()
    (x, y) = transform.map(coord[0], coord[1])
    x += shift[0]
    y += shift[1]
    painter.resetTransform()
    painter.translate(x, y)
    painter.rotate(angle)
    # Create a large rectangle and use it to find the bounding rectangle around the text.
    # Find the origin of the rectangle based on the alignment.
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
    # Draw the text
    if fill is not None:
        painter.fillRect(rect, fill)
    painter.drawText(rect, flags, text)
    # restore the original transform
    painter.setTransform(transform)

class Qt_Fig(object):
    '''
    Interface to the qt_driver, using Qt to draw the boards and template.
    '''
    def __init__(self, template, board):
        self.canvas = Qt_Plotter(template, board)
        self.transform = None

    def draw(self, template, board, bit, spacing):
        '''
        Draws the template and boards
        '''
        self.canvas.draw(template, board, bit, spacing)

    def print(self, template, board, bit, spacing):
        '''
        Prints the figure
        '''
        return self.canvas.print_fig(template, board, bit, spacing)

class Qt_Plotter(QtGui.QWidget):
    '''
    Plots the template and boards using Qt.
    '''
    def __init__(self, template, board):
        QtGui.QWidget.__init__(self)
        self.fig_width = -1
        self.fig_height = -1
        self.set_fig_dimensions(template, board)
        # if subsequent passes are less than this value, don't label
        # the pass (in intervals)
        self.sep_annotate = 4
        self.geom = None
        self.background = QtGui.QBrush(QtGui.QColor(240, 231, 201))

    def minimumSizeHint(self):
        '''
        Minimum size for this widget
        '''
        return QtCore.QSize(100, 100)

    def sizeHint(self):
        '''
        Size hint for this widget
        '''
        return QtCore.QSize(self.window_width, self.window_height)

    def set_fig_dimensions(self, template, board):
        '''
        Computes the figure dimension attributes, fig_width and fig_height, in
        intervals.
        Returns True if the dimensions changed.
        '''
        # Try default margins, but reset if the template is too small for margins
        self.margins = copy.deepcopy(OPTIONS['margins'])

        # Set the figure dimensions
        fig_width = template.length + self.margins.left + self.margins.right
        fig_height = template.height + 2 * (board.height + self.margins.sep) + \
                     self.margins.bottom + self.margins.top

        min_width = 64
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

        # The 1200 here is effectively a dpi for the screen
        scale = 1200 * board.units.intervals_to_inches(1)
        self.window_width = int(scale * fig_width)
        self.window_height = int(scale * fig_height)

        return dimensions_changed

    def draw(self, template, board, bit, spacing):
        '''
        Draws the figure
        '''
        # Generate the new geometry layout
        self.set_fig_dimensions(template, board)
        self.geom = router.Joint_Geometry(template, board, bit, spacing, self.margins)
        self.update()

    def print_fig(self, template, board, bit, spacing):
        '''
        Prints the figure
        '''
        # Generate the new geometry layout
        self.set_fig_dimensions(template, board)
        self.geom = router.Joint_Geometry(template, board, bit, spacing, self.margins)

        # Print through the preview dialog
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOrientation(QtGui.QPrinter.Landscape)
        pdialog = QtGui.QPrintPreviewDialog(printer)
        pdialog.setModal(True)
        pdialog.paintRequested.connect(self.preview_requested)
        return pdialog.exec_()

    def preview_requested(self, printer):
        '''
        Handles the print preview action.
        '''
        dpi = printer.resolution()
        painter = QtGui.QPainter()
        painter.begin(printer)
        self.paint_all(painter, dpi)
        painter.end()

    def paintEvent(self, event):
        '''
        Handles the paint event, which draws to the screen
        '''
        if self.geom is None:
            return

        painter = QtGui.QPainter(self)
        size = self.size()
        # on the screen, we add a background color:
        painter.fillRect(0, 0, size.width(), size.height(), self.background)
        # paint all of the objects
        self.window_width, self.window_height = self.paint_all(painter)
        # on the screen, highlight the active fingers
        self.draw_active_fingers(painter)
        painter.end()

    def paint_all(self, painter, dpi=None):
        '''
        Paints all the objects.

        painter: A QPainter object
        dpi: The resolution of the painter, in dots-per-inch.  If None, then
             the image is maximized in the window, but maintaining aspect ratio.
        '''
        rw = painter.window()
        window_width = rw.width()
        window_height = rw.height()

        if dpi is None:
            # transform the painter to maintain the figure aspect ratio in the current
            # window
            window_ar = float(window_width) / window_height
            fig_ar = float(self.fig_width) / self.fig_height
            if fig_ar < window_ar:
                w = my_round(fig_ar * window_height)
                painter.translate((window_width - w) // 2, window_height)
                scale = float(window_height) / self.fig_height
            else:
                h = my_round(window_width / fig_ar)
                painter.translate(0, (window_height + h) // 2)
                scale = float(window_width) / self.fig_width
        else:
            # Scale so that the image is the correct size on the page
            painter.translate(0, window_height)
            scale = float(dpi) / self.geom.board.units.intervals_per_inch
        painter.scale(scale, -scale)
        self.transform = painter.transform()

        painter.setPen(QtCore.Qt.black)

        # draw the objects
        self.draw_template(painter)
        self.draw_boards(painter)
        self.draw_title(painter)
        self.draw_finger_sizes(painter)

        return (window_width, window_height)

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
                    paint_text(painter, label, (xp, rect_T.yB), flags, shift, -90)
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
                    paint_text(painter, label, (xp, rect_T.yT()), flags, shift, -90)
    def draw_one_board(self, painter, x, y):
        '''
        Draws a single board
        '''
        painter.save()
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(0)
        painter.setPen(pen)
        if self.geom.board.icon is None:
            brush = QtGui.QBrush(QtCore.Qt.black, \
                                 QtCore.Qt.DiagCrossPattern)
            (inverted, invertable) = self.transform.inverted()
            brush.setMatrix(inverted.toAffine())
        else:
            brush = QtGui.QBrush(QtGui.QPixmap(':' + self.geom.board.icon))
        painter.setBrush(brush)
        n = len(x)
        poly = QtGui.QPolygonF()
        for i in lrange(n):
            poly.append(QtCore.QPointF(x[i], y[i]))
        painter.drawPolygon(poly)
        painter.restore()

    def draw_boards(self, painter):
        '''
        Draws all the boards
        '''
        # Plot the board center
        painter.setPen(QtCore.Qt.DashLine)
        painter.drawLine(self.geom.board_T.xMid(), self.geom.rect_T.yB, \
                         self.geom.board_T.xMid(), self.geom.board_A.yT())
        painter.setPen(QtCore.Qt.SolidLine)

        # Draw the A and B boards
        self.draw_one_board(painter, self.geom.xA, self.geom.yA)
        self.draw_one_board(painter, self.geom.xB, self.geom.yB)

        # Label the boards
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        p = (self.geom.board_A.xMid(), self.geom.board_A.yT())
        paint_text(painter, 'A', p, flags, (0, 3), fill=self.background)

        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        p = (self.geom.board_B.xMid(), self.geom.board_B.yB)
        paint_text(painter, 'B', p, flags, (0, -3), fill=self.background)

    def draw_active_fingers(self, painter):
        '''
        If the spacing supports it, highlight the active fingers and
        draw their limits
        '''
        painter.save()
        for f in self.geom.spacing.active_fingers:
            # highlight the finger rectangle
            c = self.geom.aCuts[f]
            xLT = self.geom.board_B.xL + c.xmin
            xRT = xLT + c.xmax - c.xmin
            xLB = xLT
            xRB = xRT
            if xLT > self.geom.board_B.xL:
                xLB += self.geom.bit.offset
            if xRT < self.geom.board_B.xR():
                xRB -= self.geom.bit.offset
            yT = self.geom.board_B.yT()
            yB = yT - self.geom.bit.depth
            poly = QtGui.QPolygonF()
            poly.append(QtCore.QPointF(xLT, yT))
            poly.append(QtCore.QPointF(xRT, yT))
            poly.append(QtCore.QPointF(xRB, yB))
            poly.append(QtCore.QPointF(xLB, yB))
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 75))
            painter.setBrush(brush)
            painter.drawPolygon(poly)
            painter.setPen(QtCore.Qt.red)
            painter.drawPolyline(poly)
            # draw the limits
            (xmin, xmax) = self.geom.spacing.get_limits(f)
            xmin += self.geom.board_B.xL
            xmax += self.geom.board_B.xL
            yB = self.geom.board_B.yB
            yT = self.geom.board_B.yT()
            painter.setPen(QtCore.Qt.green)
            painter.drawLine(xmin, yB, xmin, yT)
            painter.drawLine(xmax, yB, xmax, yT)
        painter.restore()

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
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        p = (self.geom.board_T.xMid(), self.margins.bottom)
        paint_text(painter, title, p, flags, (0, 5))

    def draw_finger_sizes(self, painter):
        '''
        Annotates the finger sizes on each board
        '''
        # Draw the router passes
        # ... do the B fingers, which correspond to a-Cuts
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        shift = (0, 8)
        for c in self.geom.aCuts:
            x = self.geom.board_B.xL + (c.xmin + c.xmax) // 2
            y = self.geom.board_B.yT()
            label = '%d' % (c.xmax - c.xmin)
            p = (x, y)
            paint_text(painter, label, p, flags, shift, fill=self.background)
        # ... do the A fingers, which correspond to b-Cuts
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        shift = (0, -8)
        for c in self.geom.bCuts:
            x = self.geom.board_A.xL + (c.xmin + c.xmax) // 2
            y = self.geom.board_A.yB
            label = '%d' % (c.xmax - c.xmin)
            p = (x, y)
            paint_text(painter, label, p, flags, shift, fill=self.background)

    def mousePressEvent(self, QMouseEvent):
        '''
        This is a placeholder for mouse events, and maps the clicked
        coordinate to the interval coordinate system.
        '''
        pos = QMouseEvent.pos() # in pixel coordinates
        (inverted, invertable) = self.transform.inverted()
        # map pixel coordinates to interval coords
        posM = inverted.map(pos)
        #print('posM', posM)

