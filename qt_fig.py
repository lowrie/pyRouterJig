###########################################################################
#
# Copyright 2015-2018 Robert B. Lowrie (http://github.com/lowrie)
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

from decimal import Decimal as D
import time
from PyQt5 import QtCore, QtGui, QtWidgets, QtPrintSupport
import router
import utils


def paint_text(painter, text, coord, flags, shift=(0, 0), angle=0, fill_color=None):
    '''
    Puts text at coord with alignment flags.  Returns a QRect of the bounding box
    of the text that was painted.

    painter: QPainter object
    text: The text to print.
    coord: The coordinate at which to place the text
    flags: QtCore.Qt alignment flags
    shift: Adjustments in coord, in pixels
    angle: Rotation angle
    fill_color: If not None, QColor that fills the bounding rectangle behind the text.
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
    elif flags & QtCore.Qt.AlignVCenter:
        yorg = -big // 2
    rect = QtCore.QRectF(xorg, yorg, big, big)
    rect = painter.boundingRect(rect, flags, text)
    # Draw the text
    if fill_color is not None:
        b = QtGui.QBrush(fill_color)
        painter.fillRect(rect, b)
    painter.drawText(rect, flags, text)
    # Find the text rectangle in our original coordinate system
    rect1 = painter.transform().mapRect(rect)
    (inverted, dummy_invertable) = transform.inverted()
    rect = inverted.mapRect(rect1)
    # Restore the original transform
    painter.setTransform(transform)
    return rect


class Qt_Fig(QtWidgets.QWidget):
    '''
    Interface to the qt_driver, using Qt to draw the boards and template.
    The attribute "canvas" is self, to mimic the old interface to matplotlib,
    which this class replaced.
    '''
    def __init__(self, template, boards, config):
        QtWidgets.QWidget.__init__(self)
        self.canvas = self
        self.config = config
        self.colors = {}
        self.woods = {}
        self.description = ''
        self.fig_width = -1
        self.fig_height = -1
        self.window_width = -1
        self.window_height = -1
        self.set_fig_dimensions(template, boards)
        self.geom = None
        self.dpi = 300
        self.labels = ['B', 'C', 'D', 'E', 'F']
        # font sizes are in 1/32" of an inch
        self.font_size = {'title': 4,
                          'fingers': 3,
                          'template': 3,
                          'wm_mark': 3.5,
                          'boards': 4,
                          'template_labels': 3,
                          'watermark': 4}
        self.transform = None
        self.base_transform = None
        self.mouse_pos = None
        self.scaling = 1.0
        self.translate = [0.0, 0.0]
        self.zoom_mode = False

        # Initialize keyboard modifiers
        self.shift_key = False
        self.transl = boards[0].units.transl

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

    def enable_zoom_mode(self, mode):
        '''
        Sets the zoom mode
        '''
        self.zoom_mode = mode

    def set_fig_dimensions(self, template, boards):
        '''
        Computes the figure dimension attributes, fig_width and fig_height, in
        increments.
        Returns True if the dimensions changed.
        '''
        # Try default margins, but reset if the template is too small for margins
        units = boards[0].units
        top_margin = units.abstract_to_increments(self.config.top_margin)
        bottom_margin = units.abstract_to_increments(self.config.bottom_margin)
        left_margin = units.abstract_to_increments(self.config.left_margin)
        right_margin = units.abstract_to_increments(self.config.right_margin)
        separation = units.abstract_to_increments(self.config.separation)
        self.margins = utils.Margins(separation, separation, left_margin, right_margin,
                                     bottom_margin, top_margin)

        # Set the figure dimensions
        fig_width = template.length + self.margins.left + self.margins.right
        fig_height = template.height + self.margins.bottom + self.margins.top
        for i in range(4):
            if boards[i].active:
                fig_height += boards[i].height + self.margins.sep

        if boards[3].active:
            fig_height += template.height + self.margins.sep

        if self.config.show_caul:
            fig_height += template.height + self.margins.sep

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
        scale = 1200 * boards[0].units.increments_to_inches(1)
        self.window_width = int(scale * fig_width)
        self.window_height = int(scale * fig_height)

        return dimensions_changed

    def set_colors(self, do_color):
        '''
        Sets the colors to be used from the configuration.
        '''
        color_names = ['board_background',
                       'board_foreground',
                       'canvas_background',
                       'canvas_foreground',
                       'watermark_color',
                       'template_margin_background',
                       'template_margin_foreground',
                       'pass_color',
                       'pass_alt_color',
                       'center_color']
        self.colors = {}
        for c in color_names:
            self.colors[c] = QtGui.QColor(*self.config.__dict__[c])
        if not do_color:
            for c in color_names:
                g = self.colors[c].lightness()
                self.colors[c].setRed(g)
                self.colors[c].setGreen(g)
                self.colors[c].setBlue(g)

    def draw(self, template, boards, bit, spacing, woods, description):
        '''
        Draws the figure
        '''
        # Generate the new geometry layout
        self.set_fig_dimensions(template, boards)
        self.woods = woods
        self.description = description
        self.geom = router.Joint_Geometry(template, boards, bit, spacing, self.margins,
                                          self.config)
        self.update()

    def print(self, template, boards, bit, spacing, woods, description):
        '''
        Prints the figure
        '''
        self.woods = woods
        self.description = description
        self.set_colors(self.config.print_color)

        # Generate the new geometry layout
        self.set_fig_dimensions(template, boards)
        self.geom = router.Joint_Geometry(template, boards, bit, spacing, self.margins,
                                          self.config)

        # Print through the preview dialog
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
        printer.setPageMargins(0, 0, 0, 0, QtPrintSupport.QPrinter.Inch)
        pdialog = QtPrintSupport.QPrintPreviewDialog(printer)
        pdialog.setModal(True)
        pdialog.paintRequested.connect(self.preview_requested)
        return pdialog.exec_()

    def image(self, template, boards, bit, spacing, woods, description):
        '''
        Prints the figure to a QImage object
        '''
        self.woods = woods
        self.description = description
        self.set_fig_dimensions(template, boards)
        self.geom = router.Joint_Geometry(template, boards, bit, spacing, self.margins,
                                          self.config)
        self.set_colors(True)

        if self.config.min_image_width == 0:
            self.dpi = self.config.max_image_width
            sNew = QtCore.QSize(bit.units.increments_to_inches(self.fig_width) * self.config.max_image_width,
                                bit.units.increments_to_inches(self.fig_height) * self.config.max_image_width)
        else:
            s = self.size()
            window_ar = float(s.width()) / s.height()
            fig_ar = float(self.fig_width) / self.fig_height
            if window_ar < fig_ar:
                w = s.width()
            else:
                w = int(s.height() * fig_ar)
            w = max(self.config.min_image_width, min(self.config.max_image_width, w))
            h = utils.my_round(w / fig_ar)
            sNew = QtCore.QSize(w, h)
            self.dpi = w / bit.units.increments_to_inches(self.fig_width)

        im = QtGui.QImage(sNew, QtGui.QImage.Format_RGB32)
        painter = QtGui.QPainter()
        painter.begin(im)
        size = im.size()
        if self.colors['canvas_background'] is not None:
            b = QtGui.QBrush(self.colors['canvas_background'])
            painter.fillRect(0, 0, size.width(), size.height(), b)
        self.paint_all(painter)
        painter.end()
        return im

    def preview_requested(self, printer):
        '''
        Handles the print preview action.
        '''
        dpi = printer.resolution() * self.config.print_scale_factor
        painter = QtGui.QPainter()
        painter.begin(printer)
        self.set_colors(self.config.print_color)
        self.paint_all(painter, dpi)
        painter.end()

    def paintEvent(self, dummy_event):
        '''
        Handles the paint event, which draws to the screen
        '''
        if self.geom is None:
            return

        self.set_colors(True)
        painter = QtGui.QPainter(self)
        size = self.size()
        # on the screen, we add a background color:
        if self.colors['canvas_background'] is not None:
            b = QtGui.QBrush(self.colors['canvas_background'])
            painter.fillRect(0, 0, size.width(), size.height(), b)
        # paint all of the objects
        self.window_width, self.window_height = self.paint_all(painter)
        # on the screen, highlight the active cuts
        self.draw_active_cuts(painter)
        painter.end()

    def set_font_size(self, painter, param):
        '''
        Sets the font size for font type param
        '''
        font_inches = self.font_size[param] / 32.0 * self.geom.bit.units.increments_per_inch
        dx = self.transform.map(font_inches, 0)[0] - self.transform.dx()
        font = painter.font()
        font.setPixelSize(utils.my_round(dx))
        painter.setFont(font)

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
        units = self.geom.bit.units
        scaling = self.scaling

        if dpi is None:
            # transform the painter to maintain the figure aspect ratio in the current
            # window
            window_ar = float(window_width) / window_height
            fig_ar = float(self.fig_width) / self.fig_height
            if fig_ar < window_ar:
                w = utils.my_round(fig_ar * window_height)
                painter.translate((window_width - w) // 2, window_height)
                scale = float(window_height) / self.fig_height
            else:
                h = utils.my_round(window_width / fig_ar)
                painter.translate(0, (window_height + h) // 2)
                scale = float(window_width) / self.fig_width
        else:
            # Scale so that the image is the correct size on the page
            painter.translate(0, window_height)
            scale = float(dpi) / units.increments_per_inch
            scaling = 1.0
        painter.scale(scale, -scale)

        # Save the inverse of the un-zoomed transform
        (self.base_transform, dummy_invertable) = painter.transform().inverted()

        # Apply the zoom, zooming on the current figure center
        painter.scale(scaling, scaling)
        factor = 0.5 - 0.5 / scaling
        x = self.translate[0] - self.fig_width * factor
        y = self.translate[1] - self.fig_height * factor
        painter.translate(x, y)
        self.transform = painter.transform()

        # draw the objects
        self.draw_boards(painter)
        self.draw_template(painter)
        self.draw_title(painter)
        #self.draw_finger_sizes(painter)
        if self.config.show_finger_widths:
            self.draw_finger_sizes(painter)
        return (window_width, window_height)

    def draw_passes(self, painter, blabel, cuts, y1, y2, flags, xMid,
                    is_template=True):
        '''
        Draws and labels the router passes on a template or board.

        painter: The QPainter object
        blabel: The board label (A, B, C, ...)
        cuts: Array of router.Cut objects
        y1: y-location where pass label is placed
        y2: y-location where end of line is located
        flags: Horizontal alignment for label
        xMid: x-location of board center
        is_template: If true, then a template

        Returns the pass label if a pass matches xMid, None otherwise
        '''
        board_T = self.geom.board_T
        shift = (0, 0)  # for adjustments of text
        passMid = None  # location of board-center pass (return value)
        font_type = 'template'
        char_size = self.font_size[font_type]
        self.set_font_size(painter, font_type)
        # Collect the router pass locations in a single array by looping
        # through each cut and each pass for each cut, right-to-left.
        xp = []
        for c in cuts[::-1]:
            for p in range(len(c.passes) - 1, -1, -1):
                xp.append(c.passes[p])
        # Loop through the passes and do the labels
        np = len(xp)
        for i in range(np):
            # Determine vertical alignment, by checking the separation from adjacent passes.
            # If too close to an adjacent pass, then shift the alignment in the opposite
            # direction.
            flagsv = flags
            diffm = xp[max(0, i - 1)] - xp[i]
            diffp = xp[i] - xp[min(np - 1, i + 1)]
            if i == 0:
                if diffp < char_size:
                    flagsv |= QtCore.Qt.AlignTop
                else:
                    flagsv |= QtCore.Qt.AlignVCenter
            elif i == np - 1:
                if diffm < char_size:
                    flagsv |= QtCore.Qt.AlignBottom
                else:
                    flagsv |= QtCore.Qt.AlignVCenter
            elif diffp < char_size:
                if diffm < char_size:
                    flagsv |= QtCore.Qt.AlignVCenter
                else:
                    flagsv |= QtCore.Qt.AlignTop
            else:
                if diffm < char_size:
                    flagsv |= QtCore.Qt.AlignBottom
                else:
                    flagsv |= QtCore.Qt.AlignVCenter
            xpShift = xp[i] + board_T.xL()
            # Draw the text label for this pass
            label = ''
            this_is_midpoint = False
            if is_template or self.config.show_router_pass_identifiers:
                label = '%d%s' % (i + 1, blabel)
                if xpShift == xMid:
                    passMid = label
                    this_is_midpoint = True
            if not is_template and self.config.show_router_pass_locations:
                if label:
                    label += ': '
                loc = self.geom.bit.units.increments_to_string(board_T.xR() - xpShift)
                label += loc
            painter.save()
            if this_is_midpoint and is_template:
                pen = painter.pen()
                pen.setColor(self.colors['center_color'])
                painter.setPen(pen)
            r = paint_text(painter, label, (xpShift, y1), flagsv, shift, -90)
            # Determine the line starting point from the size of the text.
            # Create a small margin so that the starting point is not too
            # close to the text.
            y1text = y1
            if y1 > y2:
                y1text = r.y()
                if y1text > y2:
                    y1text += 0.05 * (y2 - y1text)
            else:
                y1text = r.y() + r.height()
                if y1text < y2:
                    y1text += 0.05 * (y2 - y1text)
            # If there is any room left, draw the line from the label to the base of cut
            if (y1 - y2) * (y1text - y2) > 0:
                p1 = QtCore.QPointF(xpShift, y1text)
                p2 = QtCore.QPointF(xpShift, y2)
                painter.drawLine(p1, p2)
            painter.restore()
        return passMid

    def draw_alignment(self, painter):
        '''
        Draws the alignment lines on all templates
        '''
        board_T = self.geom.board_T
        board_TDD = self.geom.board_TDD
        board_caul = self.geom.board_caul

        # draw the alignment lines on both templates
        x = board_T.xR() # + self.geom.bit.width // 2

        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setColor(self.colors['template_margin_foreground'])
        pen.setWidthF(self.config.line_width) #0

        bg_pen = QtGui.QPen(QtCore.Qt.SolidLine)
        bg_pen.setColor(QtGui.QColor('White'))
        bg_pen.setWidthF(0)

        self.set_font_size(painter, 'wm_mark')
        mrk_font = painter.font()
        mrk_font.setBold(True)
        x1 = painter.fontMetrics().height()

        self.set_font_size(painter, 'template')
        lbl_font = painter.font()
        label = self.transl.tr(u'\u2b9c ALIGN');
        #flags = QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter
        flags = QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        for b in [board_T, board_TDD, board_caul]:
            if b is not None:
                y1 = b.yB()
                y2 = b.yT()
                painter.setPen(pen)
                painter.drawLine(x, y1, x, y2)
                #paint_text(painter, label, (x, (y1 + y2) // 2), flags, (0, 0), -90)
                if self.description is not None:
                    painter.setFont(mrk_font)
                    paint_text(painter, self.description, (x, (y1 + y2) // 2), flags, (x1, 0), -90)
                    painter.setFont(lbl_font)
                painter.setPen(bg_pen)
                painter.drawLine(QtCore.QPointF(x-0.5, y1+0.5), QtCore.QPointF(x-0.5, y2-0.5))
                painter.drawLine(QtCore.QPointF(x+0.5, y1+0.5), QtCore.QPointF(x+0.5, y2-0.5))
                painter.setPen(pen)
                paint_text(painter, label, ( ( x ), ( y2 - 1 )) , flags, (0, 0), 0)


    def draw_template_rectangle(self, painter, r, b):
        '''
        Draws the geometry of a template
        '''
        # Fill the entire template as white
        painter.fillRect(r.xL(), r.yB(), r.width, r.height, QtCore.Qt.white)

        # Fill the template margins with a grayshade
        brush = QtGui.QBrush(QtGui.QColor(self.colors['template_margin_background']))
        painter.fillRect(r.xL(), r.yB(), b.xL() - r.xL(), r.height, brush)
        painter.fillRect(b.xR(), r.yB(), r.xR() - b.xR(), r.height, brush)

        # Draw the template bounding box
        painter.drawRect(r.xL(), r.yB(), r.width, r.height)

        # Label the template with a watermark
        if self.description is not None:
            painter.save()
            self.set_font_size(painter, 'watermark')
            painter.setPen(self.colors['watermark_color'])
            flags = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter
            x = r.xL() + r.width // 2
            y = r.yB() + r.height // 2
            paint_text(painter, self.description, (x, y), flags)
            painter.restore()

    def draw_template(self, painter):
        '''
        Draws the Incra templates
        '''
        rect_T = self.geom.rect_T
        board_T = self.geom.board_T
        boards = self.geom.boards

        xMid = board_T.xMid()
        centerline = []
        centerline_TDD = []

        pen_canvas = QtGui.QPen(QtCore.Qt.SolidLine)
        pen_canvas.setColor(self.colors['canvas_foreground'])
        pen_canvas.setWidthF(0)
        penA = QtGui.QPen(QtCore.Qt.SolidLine)
        penA.setColor(self.colors['pass_color'])
        penA.setWidthF(self.config.line_width) # 0
        penB = QtGui.QPen(QtCore.Qt.DashLine)
        penB.setColor(self.colors['pass_alt_color'])
        penB.setWidthF(self.config.line_width) # 0

        painter.setPen(pen_canvas)
        self.draw_template_rectangle(painter, rect_T, board_T)

        if boards[3].active:
            rect_TDD = self.geom.rect_TDD
            board_TDD = self.geom.board_TDD
            self.draw_template_rectangle(painter, rect_TDD, board_TDD)
            rect_top = rect_TDD
        else:
            rect_top = rect_T

        flagsL = QtCore.Qt.AlignLeft
        flagsR = QtCore.Qt.AlignRight
        show_passes = self.config.show_router_pass_identifiers |\
                      self.config.show_router_pass_locations

        frac_depth = 0.95 * self.geom.bit.depth
        sepOver2 = 0.5 * self.geom.margins.sep
        # Draw the router passes
        # ... do the top board passes
        y1 = boards[0].yB() - sepOver2
        y2 = boards[0].yB() + frac_depth
        painter.setPen(penA)
        pm = self.draw_passes(painter, 'A', boards[0].bottom_cuts, rect_top.yMid(),
                              rect_top.yT(), flagsR, xMid)
        if pm is not None:
            if boards[3].active:
                centerline_TDD.append(pm)
            else:
                centerline.append(pm)
        if show_passes:
            painter.setPen(pen_canvas)
            self.draw_passes(painter, 'A', boards[0].bottom_cuts, y1, y2,
                             flagsL, xMid, False)

        # bit and board information lables
        label_size = 'L:{}'.format(self.geom.bit.units.increments_to_string(self.geom.boards[0].width, True))
        label_height = 'h:{}'.format(self.geom.bit.units.increments_to_string(self.geom.bit.depth, False))
        label_bit = ''

        if self.geom.bit.angle > 0:
            label_bit += 'V:{}\xb0 '.format(self.geom.bit.angle)
            if abs(self.geom.bit.gap) > utils.Units.quant:
                label_height += '/{}'.format(self.geom.bit.units.increments_to_string(self.geom.bit.depth_0, True))

        label_bit += '\xd8{}'.format(self.geom.bit.units.increments_to_string(self.geom.bit.width, True))

        label_bottom = 'A,B'
        label_top = None
        i = 0
        # Do double-double passes
        if boards[3].active:
            y1 = boards[3].yT() + sepOver2
            y2 = boards[3].yT() - frac_depth
            painter.setPen(penB)
            pm = self.draw_passes(painter, self.labels[i], boards[3].top_cuts, rect_TDD.yMid(),
                                  rect_TDD.yT(), flagsR, xMid)
            if pm is not None:
                centerline_TDD.append(pm)
            if show_passes:
                painter.setPen(pen_canvas)
                self.draw_passes(painter, self.labels[i], boards[3].top_cuts, y1, y2,
                                 flagsR, xMid, False)

            y1 = boards[3].yB() - sepOver2
            y2 = boards[3].yB() + frac_depth
            painter.setPen(penA)
            pm = self.draw_passes(painter, self.labels[i + 1], boards[3].bottom_cuts,
                                  rect_TDD.yMid(), rect_TDD.yB(), flagsL, xMid)
            if pm is not None:
                centerline_TDD.append(pm)
            if show_passes:
                painter.setPen(pen_canvas)
                self.draw_passes(painter, self.labels[i + 1], boards[3].bottom_cuts, y1, y2,
                                 flagsL, xMid, False)
            label_bottom = 'D,E,F'
            label_top = 'A,B,C'
            i += 2
        # Do double passes
        if boards[2].active:
            y1 = boards[2].yT() + sepOver2
            y2 = boards[2].yT() - frac_depth
            if boards[3].active:
                painter.setPen(penA)
            else:
                painter.setPen(penB)
            pm = self.draw_passes(painter, self.labels[i], boards[2].top_cuts, rect_T.yMid(),
                                  rect_T.yT(), flagsR, xMid)
            if pm is not None:
                centerline.append(pm)
            if show_passes:
                painter.setPen(pen_canvas)
                self.draw_passes(painter, self.labels[i], boards[2].top_cuts, y1, y2,
                                 flagsR, xMid, False)
            y1 = boards[2].yB() - sepOver2
            y2 = boards[2].yB() + frac_depth
            painter.setPen(penA)
            pm = self.draw_passes(painter, self.labels[i + 1], boards[2].bottom_cuts, rect_T.yMid(),
                                  rect_T.yB(), flagsL, xMid)
            if pm is not None:
                centerline.append(pm)
            if show_passes:
                painter.setPen(pen_canvas)
                self.draw_passes(painter, self.labels[i + 1], boards[2].bottom_cuts, y1, y2,
                                 flagsL, xMid, False)
            if not boards[3].active:
                label_bottom = 'A,B,C,D'
            i += 2

        # ... do the bottom board passes
        y1 = boards[1].yT() + sepOver2
        y2 = boards[1].yT() - frac_depth
        if boards[2].active or boards[3].active:
            painter.setPen(penB)
        else:
            painter.setPen(penA)
        pm = self.draw_passes(painter, self.labels[i], boards[1].top_cuts, rect_T.yMid(),
                              rect_T.yB(), flagsL, xMid)
        if pm is not None:
            centerline.append(pm)
        if show_passes:
            painter.setPen(pen_canvas)
            self.draw_passes(painter, self.labels[i], boards[1].top_cuts, y1, y2,
                             flagsR, xMid, False)

        flagsLC = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        flagsRC = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

        # ... draw the caul template and do its passes.  Draw events may be
        # triggered before we have the ability to recreate the geom object,
        # so we have to ensure the caul_top object actually exists.
        datetime = time.strftime('\n%d %b %y\n%H:%M', time.localtime())
        if self.config.show_caul and self.geom.caul_top is not None:
            rect_caul = self.geom.rect_caul
            board_caul = self.geom.board_caul
            top = self.geom.caul_top
            bottom = self.geom.caul_bottom
            self.draw_template_rectangle(painter, rect_caul, board_caul)
            centerline_caul = []
            painter.setPen(penA)
            pm = self.draw_passes(painter, 'A', top, rect_caul.yMid(), rect_caul.yT(), flagsR, xMid)
            if pm is not None:
                centerline_caul.append(pm)
            pm = self.draw_passes(painter, self.labels[i], bottom, rect_caul.yMid(),
                                  rect_caul.yB(), flagsL, xMid)
            if pm is not None:
                centerline_caul.append(pm)
            self.set_font_size(painter, 'template_labels')
            label = self.transl.tr('Cauls')
            if centerline_caul:
                label += self.transl.tr('\nCenter: ') + centerline_caul[0]
            else:
                pen = QtGui.QPen(QtCore.Qt.DashLine)
                pen.setColor(self.colors['center_color'])
                pen.setWidthF(0)
                painter.setPen(pen)
                painter.drawLine(xMid, rect_caul.yB(), xMid, rect_caul.yT())
            painter.setPen(self.colors['template_margin_foreground'])
            paint_text(painter, label + datetime, (rect_caul.xL(), rect_caul.yMid()),
                       flagsLC, (5, 0))
            paint_text(painter, label, (rect_caul.xR(), rect_caul.yMid()), flagsRC, (-5, 0))

        # Label the templates
        pen = QtGui.QPen(QtCore.Qt.DashLine)
        pen.setColor(self.colors['center_color'])
        pen.setWidthF(0)
        self.set_font_size(painter, 'template_labels')
        label_center = ' '
        if centerline:
            label_bottom += self.transl.tr('\nCenter: ') + centerline[0]

        else:
            painter.setPen(pen)
            painter.drawLine(xMid, rect_T.yB(), xMid, rect_T.yT())

        painter.setPen(self.colors['template_margin_foreground'])

        label_left  = '\n'+ label_bit + '\n' + label_height + label_center + label_size
        label_right = label_center + datetime

        paint_text(painter, label_bottom + label_left, (rect_T.xL(), rect_T.yMid()), flagsLC, (5, 0))
        paint_text(painter, label_bottom + label_right, (rect_T.xR(), rect_T.yMid()), flagsRC, (-5, 0))

        if label_top is not None:
            if centerline_TDD:
                label_top += self.transl.tr('\nCenter: ') + centerline_TDD[0]
            else:
                painter.setPen(pen)
                painter.drawLine(xMid, rect_TDD.yB(), xMid, rect_TDD.yT())
            painter.setPen(self.colors['template_margin_foreground'])
            paint_text(painter, label_top + label_left, (rect_TDD.xL(), rect_TDD.yMid()),
                       flagsLC, (5, 0))
            paint_text(painter, label_top + label_right, (rect_TDD.xR(), rect_TDD.yMid()),
                       flagsRC, (-5, 0))

        self.draw_alignment(painter)

    def draw_one_board(self, painter, board, bit, fill_color):
        '''
        Draws a single board
        '''
        if not board.active:
            return
        # form the polygon to draw
        (x, y) = board.perimeter(bit)
        n = len(x)
        poly = QtGui.QPolygonF()
        for i in range(n):
            poly.append(QtCore.QPointF(x[i], y[i]))
        # paint it
        painter.save()
        pen = QtGui.QPen(self.colors['board_foreground'])
        pen.setWidthF(0)
        painter.setPen(pen)
        icon = self.woods[board.wood]
        if icon is not None:
            if isinstance(icon, str):
                # then it's an image file
                brush = QtGui.QBrush(QtGui.QPixmap(icon))
            else:
                # oterhwise, if must be a pattern fill
                if icon == QtCore.Qt.SolidPattern:
                    color = fill_color
                else:
                    # It's not a solid fill, so the polygon with the background color, first
                    color = self.colors['board_background']
                    brush = QtGui.QBrush(color)
                    painter.setBrush(brush)
                    painter.drawPolygon(poly)
                    color = self.colors['board_foreground']
                brush = QtGui.QBrush(color, icon)
            (inverted, dummy_invertable) = self.transform.inverted()
            # setMatrix is not offered anymore
            # brush.setMatrix(inverted.toAffine())
            brush.setTransform(inverted)
            painter.setBrush(brush)
        painter.drawPolygon(poly)
        painter.restore()

    def draw_boards(self, painter):
        '''
        Draws all the boards
        '''

        # Draw all of the boards
        for i in range(4):
            self.draw_one_board(painter, self.geom.boards[i], self.geom.bit,
                                self.colors['board_background'])

        # Label the boards
        if self.config.show_router_pass_identifiers or self.config.show_router_pass_locations:
            self.set_font_size(painter, 'boards')
            pen = QtGui.QPen(QtCore.Qt.SolidLine)
            pen.setColor(self.colors['canvas_foreground'])
            pen.setWidthF(0)
            painter.setPen(pen)

            x1 = self.geom.boards[0].xL() - self.geom.bit.width // 2
            x2 = self.geom.boards[0].xL() - self.geom.bit.width // 4
            flags = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

            y = self.geom.boards[0].yB()
            p = (x1, y)
            paint_text(painter, 'A', p, flags, (-3, 0))
            painter.drawLine(x1, y, x2, y)

            i = 0  # index in self.labels

            if self.geom.boards[3].active:
                y = self.geom.boards[3].yT()
                p = (x1, y)
                paint_text(painter, 'B', p, flags, (-3, 0))
                painter.drawLine(x1, y, x2, y)
                y = self.geom.boards[3].yB()
                p = (x1, y)
                paint_text(painter, 'C', p, flags, (-3, 0))
                painter.drawLine(x1, y, x2, y)
                i = 2
            if self.geom.boards[2].active:
                y = self.geom.boards[2].yT()
                p = (x1, y)
                paint_text(painter, self.labels[i], p, flags, (-3, 0))
                painter.drawLine(x1, y, x2, y)
                y = self.geom.boards[2].yB()
                p = (x1, y)
                paint_text(painter, self.labels[i + 1], p, flags, (-3, 0))
                painter.drawLine(x1, y, x2, y)
                i += 2

            y = self.geom.boards[1].yT()
            p = (x1, y)
            paint_text(painter, self.labels[i], p, flags, (-3, 0))
            painter.drawLine(x1, y, x2, y)

    def cut_polygon(self, c):
        '''
        Forms the polygon for the cut corresponding to the cut c
        '''
        boards = self.geom.boards
        xLT = boards[0].xL() + c.xmin
        xRT = boards[0].xL() + c.xmax
        xLB = xLT
        xRB = xRT
        if c.xmin > 0:
            xLB += self.geom.bit.overhang
        if c.xmax < self.geom.boards[0].width:
            xRB -= self.geom.bit.overhang
        yB = boards[0].yB()
        yT = yB + self.geom.bit.depth
        poly = QtGui.QPolygonF()
        poly.append(QtCore.QPointF(xLT, yT))
        poly.append(QtCore.QPointF(xRT, yT))
        poly.append(QtCore.QPointF(xRB, yB))
        poly.append(QtCore.QPointF(xLB, yB))
        poly.append(QtCore.QPointF(xLT, yT))
        return poly

    def draw_active_cuts(self, painter):
        '''
        If the spacing supports it, highlight the active cuts and
        draw their limits
        '''

        f = self.geom.spacing.cursor_cut
        if f is None:
            return

        pen = QtGui.QPen()
        pen.setWidthF(0)

        # get the perimeter of the cursor
        cursor_poly = self.cut_polygon(self.geom.boards[0].bottom_cuts[f])

        # initialize limits
        xminG = self.geom.boards[0].width
        xmaxG = 0

        # draw the active cuts filled, and track the limits
        painter.save()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 75))
        painter.setBrush(brush)
        pen.setColor(QtCore.Qt.red)
        painter.setPen(pen)
        fcolor = QtGui.QColor(self.colors['board_background'])
        fcolor.setAlphaF(1.0)
        for f in self.geom.spacing.active_cuts:
            poly = self.cut_polygon(self.geom.boards[0].bottom_cuts[f])
            painter.drawPolygon(poly)
            # keep track of the limits
            (xmin, xmax) = self.geom.spacing.get_limits(f)
            xminG = min(xminG, xmin)
            xmaxG = max(xmaxG, xmax)
            # label the polygon with its index
            xText = 0.5 * (poly[0].x() + poly[1].x())
            yText = 0.5 * (poly[0].y() + poly[1].y())
            text = '%d' % f
            flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
            paint_text(painter, text, (xText, yText), flags, (0, -5),
                       fill_color=fcolor)
        painter.restore()

        # draw the limits
        # using QPointF to avoid border marks overlap with cursor
        painter.save()
        xminG += self.geom.boards[0].xL()
        xmaxG += self.geom.boards[0].xL()
        yB = self.geom.boards[0].yB()
        yT = self.geom.boards[0].yT()
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        half = D('0.5')
        painter.drawLine(QtCore.QPointF(xminG - half, yB), QtCore.QPointF(xminG - half, yT))
        painter.drawLine(QtCore.QPointF(xmaxG + half, yB), QtCore.QPointF(xmaxG + half, yT))
        painter.restore()

        # draw the perimeter of the cursor cut at the end to get it always visible
        painter.save()
        pen.setColor(QtCore.Qt.blue)
        painter.setPen(pen)
        painter.drawPolyline(cursor_poly)
        painter.restore()

    def draw_title(self, painter):
        '''
        Draws the title
        '''

        self.set_font_size(painter, 'title')
        painter.setPen(self.colors['canvas_foreground'])
        title = router.create_title(self.geom.boards, self.geom.bit, self.geom.spacing)
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        p = (self.geom.board_T.xMid(), self.margins.bottom)
        paint_text(painter, title, p, flags, (0, 5))

        self.set_font_size(painter, 'template')
        title = '{}x{}'.format(
            self.geom.bit.units.increments_to_string(self.fig_width),
            self.geom.bit.units.increments_to_string(self.fig_height, True)
        )
        paint_text(painter, title, (self.margins.left, self.fig_height),
                   QtCore.Qt.AlignBaseline | QtCore.Qt.AlignLeft)

    def draw_finger_sizes(self, painter):
        '''
        Annotates the finger sizes on each board
        with 3 digit precision
        '''
        units = self.geom.bit.units
        self.set_font_size(painter, 'template')
        painter.setPen(self.colors['board_foreground'])
        fcolor = QtGui.QColor(self.colors['board_background'])
        fcolor.setAlphaF(1.0)
        # Determine the cuts that are adjacent to board-A and board-B
        acuts = self.geom.boards[1].top_cuts
        bcuts = self.geom.boards[0].bottom_cuts
        if self.geom.boards[2].active:
            bcuts = self.geom.boards[2].bottom_cuts
            if self.geom.boards[3].active:
                acuts = self.geom.boards[3].top_cuts
            else:
                acuts = self.geom.boards[2].top_cuts
        # Draw the router passes
        # ... do the B cuts
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        shift = (0, 8)
        for c in bcuts:
            x = self.geom.boards[1].xL() + (c.xmin + c.xmax) // 2
            y = self.geom.boards[1].yT()
            label = units.increments_to_string(round(c.xmax - c.xmin, 3))
            p = (x, y)
            paint_text(painter, label, p, flags, shift, fill_color=fcolor)
        # ... do the A cuts
        flags = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        shift = (0, -8)
        for c in acuts:
            x = self.geom.boards[0].xL() + (c.xmin + c.xmax) // 2
            y = self.geom.boards[0].yB()
            label = units.increments_to_string(round(c.xmax - c.xmin, 3))
            p = (x, y)
            paint_text(painter, label, p, flags, shift, fill_color=fcolor)

    def keyPressEvent(self, event):
        '''
        Handles key press events.  At this level, we handle zooming.
        '''

        if not self.zoom_mode:
            event.ignore()
            return

        # Keyboard zooming mode works only if the shift key is pressed.
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = True
        elif event.key() == QtCore.Qt.Key_Escape:
            self.scaling = 1.0
            self.translate = [0.0, 0.0]
            self.update()
        elif not self.shift_key:
            event.ignore()
            return

        dx = 4.0 / self.scaling
        scale_factor = 1.1

        if event.key() == QtCore.Qt.Key_Left:
            self.translate[0] -= dx
            self.update()
        elif event.key() == QtCore.Qt.Key_Right:
            self.translate[0] += dx
            self.update()
        elif event.key() == QtCore.Qt.Key_Up:
            self.translate[1] += dx
            self.update()
        elif event.key() == QtCore.Qt.Key_Down:
            self.translate[1] -= dx
            self.update()
        elif event.key() == QtCore.Qt.Key_Z:
            self.scaling *= scale_factor
            self.update()
        elif event.key() == QtCore.Qt.Key_X:
            self.scaling /= scale_factor
            self.update()
        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        '''
        Handles key release events
        '''
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_key = False
        else:
            event.ignore()

    def wheelEvent(self, event):
        '''
        Handles mouse wheel events, which is used for zooming in and out.
        '''
        if not self.zoom_mode:
            event.ignore()
            return

        if self.config.debug:
            print('qt_fig.wheelEvent', event.angleDelta())
        ppp = event.angleDelta() / 120
        self.scaling *= 1 + 0.05 * ppp.y()
        self.update()

    def mousePressEvent(self, event):
        '''
        Handles mouse button press:
           left: start a move at that location
           right: reset view
        '''
        if not self.zoom_mode:
            event.ignore()
            return

        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_pos = self.base_transform.map(event.pos())
            if self.config.debug:
                print('mouse pressed here: {} {}'.format(self.mouse_pos.x(),
                                                         self.mouse_pos.y()))
        elif event.button() == QtCore.Qt.RightButton:
            self.scaling = 1.0
            self.translate = [0.0, 0.0]
            self.update()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        '''
        Handles mouse button release:
           left: end the move
        '''
        if not self.zoom_mode:
            event.ignore()
            return

        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_pos = None
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        '''
        Handles mouse move, when a button is pressed.  In this case, we keep track
        of the translation under zoom.
        '''
        if not self.zoom_mode or self.mouse_pos is None:
            event.ignore()
            return

        pos = self.base_transform.map(event.localPos())
        if self.config.debug:
            print('mouse moved here: {} {}'.format(pos.x(), pos.y()))
        diffx = (pos.x() - self.mouse_pos.x())
        diffy = (pos.y() - self.mouse_pos.y())
        if abs(diffx) + abs(diffy) > 1:  # avoid teeny-tiny moves
            self.translate[0] += diffx / self.scaling
            self.translate[1] += diffy / self.scaling
            self.mouse_pos = pos
            self.update()
