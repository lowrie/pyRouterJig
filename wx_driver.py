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
Contains the main driver, using wxPython.

TODO:

Bugs:
- Can't use tick labels on sliders, because they won't hide.
- Redrawing after changing board size doesn't autofit within window
  size properly.
- First use of variable spacing puts its slider in mpl region.  Resizing the window fixes it.
  Might be related to redrawing bug.

Features:
- Enable use of arrows for sliders.
- Tooltips for each input.
- Make fold-over templates, appropriate for hand cut.
- Documentation
- More friendly error messages and handling.

Other:
- Should we really be forcing board and bit dimensions to be exact
  multiples of intervals?
- Replace matplotlib with direct wxPython graphics?  Need to make sure
  printing works as well. 
'''

import os, sys, traceback
import wx
import router
import mpl
import spacing
import utils
#import wx.lib.inspection

from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

class WX_Driver(wx.Frame):
    ''' wxPython driver for MPL_Plotter
    '''
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'pyRouterJig')
#        sys.excepthook = self.exception_hook

        self.create_menu()
        self.create_status_bar()

        self.board = router.Board(width=utils.inches_to_intervals(7.5))
        self.bit = router.Router_Bit(16, 24)
        self.template = router.Incra_Template(self.board)
        self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board)
        self.equal_spacing.set_cuts()
        self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
        self.var_spacing.set_cuts()
        self.spacing = self.equal_spacing # the default
        self.mpl = mpl.MPL_Plotter()

        self.create_main_panel()
        self.draw_mpl()

    def exception_hook(self, etype, value, trace):
        '''
        Handler for all exceptions.

        :param `etype`: the exception type (`SyntaxError`, `ZeroDivisionError`, etc...);
        :type `etype`: `Exception`
        :param string `value`: the exception error message;
        :param string `trace`: the traceback header, if any (otherwise, it prints the
         standard Python header: ``Traceback (most recent call last)``.
        '''

        tmp = traceback.format_exception(etype, value, trace)
        exception = '\n'.join(tmp)

        dlg = wx.MessageDialog(self, exception, 'ERROR!', wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()    

    def create_menu(self):
        '''
        Creates the drop-down menu.
        '''
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        menu_help = wx.Menu()
        m_about = menu_help.Append(-1, "&About\tF1", "About the demo")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_help, "&Help")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        '''
        Creates the main panel with all the controls on it:
          * mpl canvas 
          * mpl navigation toolbar
          * Control panel for interaction
        '''
        self.panel = wx.Panel(self)
        
        # Create the mpl Figure and FigCanvas objects. 
        self.dpi = 100
        self.canvas = FigCanvas(self.panel, -1, self.mpl.fig)
        
        # Board width text box
        self.tb_board_width_label = wx.StaticText(self.panel, -1, 'Board Width')
        self.tb_board_width = wx.TextCtrl(
            self.panel, 
            size=(80,-1),
            style=wx.TE_PROCESS_ENTER)
        self.tb_board_width.Bind(wx.EVT_TEXT_ENTER, self.on_board_width)
        
        # Bit width text box
        self.tb_bit_width_label = wx.StaticText(self.panel, -1, 'Bit Width')
        self.tb_bit_width = wx.TextCtrl(
            self.panel, 
            size=(80,-1),
            style=wx.TE_PROCESS_ENTER)
        self.tb_bit_width.Bind(wx.EVT_TEXT_ENTER, self.on_bit_width)
        
        # Bit depth text box
        self.tb_bit_depth_label = wx.StaticText(self.panel, -1, 'Bit Depth')
        self.tb_bit_depth = wx.TextCtrl(
            self.panel, 
            size=(80,-1),
            style=wx.TE_PROCESS_ENTER)
        self.tb_bit_depth.Bind(wx.EVT_TEXT_ENTER, self.on_bit_depth)
        
        # Bit angle text box
        self.tb_bit_angle_label = wx.StaticText(self.panel, -1, 'Bit Angle')
        self.tb_bit_angle = wx.TextCtrl(
            self.panel, 
            size=(80,-1),
            style=wx.TE_PROCESS_ENTER)
        self.tb_bit_angle.Bind(wx.EVT_TEXT_ENTER, self.on_bit_angle)
        
        self.drawbutton = wx.Button(self.panel, -1, "Draw")
        self.drawbutton.Bind(wx.EVT_BUTTON, self.on_draw_button)

        # Combo for the spacing option
        self.current_spacing = 'Equal'
        self.combo_spacing_label = wx.StaticText(self.panel, -1, 'Spacing')
        self.combo_spacing = wx.ComboBox(self.panel, value=self.current_spacing, \
                                         choices=['Equal', 'Variable'],
                                         style=wx.CB_READONLY)
        self.combo_spacing.SetValue(self.current_spacing)
        self.combo_spacing.Bind(wx.EVT_COMBOBOX, self.on_combo_spacing)

        # Create the controllers for all the spacing options.  Below, the spacing options 
        # that are not active will be hidden.

        # Slider labels are not hid when using Hide(), so don't use them
        #style_sliders = wx.SL_AUTOTICKS | wx.SL_LABELS
        style_sliders = wx.SL_AUTOTICKS

        #############################
        # Equal spacing options
        #############################
        
        self.equal_spacing_params = self.equal_spacing.get_params()
        self.es_cut_values = [0] * 3

        # First slider
        p = self.equal_spacing_params[0]
        self.es_cut_values[0] = p.vInit
        self.es_slider0_label = wx.StaticText(self.panel, -1, p.label)
        self.es_slider0 = wx.Slider(self.panel, -1, 
                                    value=p.vInit, 
                                    minValue=p.vMin,
                                    maxValue=p.vMax,
                                    style=style_sliders)
        self.es_slider0.SetTickFreq(1, 1)
        self.es_slider0.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_es_slider0)
        self.es_slider0.Bind(wx.EVT_KEY_DOWN, self.on_es_slider0_key, self.es_slider0)

        # Second slider
        p = self.equal_spacing_params[1]
        self.es_cut_values[1] = p.vInit
        self.es_slider1_label = wx.StaticText(self.panel, -1, p.label)
        self.es_slider1 = wx.Slider(self.panel, -1, 
                                    value=p.vInit, 
                                    minValue=p.vMin,
                                    maxValue=p.vMax,
                                    style=style_sliders)
        self.es_slider1.SetTickFreq(1, 1)
        self.es_slider1.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_es_slider1)

        # Check box for centering
        p = self.equal_spacing_params[2]
        self.es_cut_values[2] = p.vInit
        self.cb_es_centered = wx.CheckBox(self.panel, -1, 
            p.label,
            style=wx.ALIGN_RIGHT)
        self.cb_es_centered.SetValue(p.vInit)
        self.cb_es_centered.Bind(wx.EVT_CHECKBOX, self.on_cb_es_centered)

        #############################
        # Variable spacing options
        #############################
        
        self.var_spacing_params = self.var_spacing.get_params()
        self.vs_cut_values = [0] * 2

        # First slider
        p = self.var_spacing_params[0]
        self.vs_cut_values[0] = p.vInit
        self.vs_slider0_label = wx.StaticText(self.panel, -1, p.label)
        self.vs_slider0 = wx.Slider(self.panel, -1, 
                                    value=p.vInit, 
                                    minValue=p.vMin,
                                    maxValue=p.vMax,
                                    style=style_sliders)
        self.vs_slider0.SetTickFreq(1, 1)
        self.vs_slider0.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_vs_slider0)

        ##### Done with spacing options

        # Create the navigation toolbar, tied to the canvas
        self.toolbar = NavigationToolbar(self.canvas)
#        self.toolbar.ToggleTool(self.toolbar.wx_ids['Pan'], False)
#        self.toolbar.ToggleTool(self.toolbar.wx_ids['Zoom'], False)

        ########################
        # Layout with box sizers
        ########################
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.SHAPED | wx.ALL)
        self.vbox.Add(self.toolbar, 0, wx.EXPAND)
        self.vbox.AddSpacer(10)
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL

        self.hbox.Add(self.drawbutton, 0, border=3, flag=flags)
        self.hbox.AddSpacer(30)

        self.vbox_board_width = wx.BoxSizer(wx.VERTICAL)
        self.vbox_board_width.Add(self.tb_board_width_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_board_width.Add(self.tb_board_width, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox.Add(self.vbox_board_width, 0, flag=flags)

        self.vbox_bit_width = wx.BoxSizer(wx.VERTICAL)
        self.vbox_bit_width.Add(self.tb_bit_width_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_bit_width.Add(self.tb_bit_width, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox.Add(self.vbox_bit_width, 0, flag=flags)

        self.vbox_bit_depth = wx.BoxSizer(wx.VERTICAL)
        self.vbox_bit_depth.Add(self.tb_bit_depth_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_bit_depth.Add(self.tb_bit_depth, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox.Add(self.vbox_bit_depth, 0, flag=flags)

        self.vbox_bit_angle = wx.BoxSizer(wx.VERTICAL)
        self.vbox_bit_angle.Add(self.tb_bit_angle_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_bit_angle.Add(self.tb_bit_angle, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox.Add(self.vbox_bit_angle, 0, flag=flags)
        self.hbox.AddSpacer(30)

        self.vbox_combo_spacing = wx.BoxSizer(wx.VERTICAL)
        self.vbox_combo_spacing.Add(self.combo_spacing_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_combo_spacing.Add(self.combo_spacing, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox.Add(self.vbox_combo_spacing, 0, flag=flags)

        self.hbox_es = wx.BoxSizer(wx.HORIZONTAL)

        self.vbox_es_slider0 = wx.BoxSizer(wx.VERTICAL)
        self.vbox_es_slider0.Add(self.es_slider0_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_es_slider0.Add(self.es_slider0, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox_es.Add(self.vbox_es_slider0, 0, flag=flags)
        
        self.vbox_es_slider1 = wx.BoxSizer(wx.VERTICAL)
        self.vbox_es_slider1.Add(self.es_slider1_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_es_slider1.Add(self.es_slider1, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox_es.Add(self.vbox_es_slider1, 0, flag=flags)
        
        self.hbox_es.Add(self.cb_es_centered, 0, border=3, flag=flags)
        self.hbox.Add(self.hbox_es, 0, flag=flags)

        self.hbox_vs = wx.BoxSizer(wx.HORIZONTAL)

        self.vbox_vs_slider0 = wx.BoxSizer(wx.VERTICAL)
        self.vbox_vs_slider0.Add(self.vs_slider0_label, 0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.vbox_vs_slider0.Add(self.vs_slider0, 0, border=3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        self.hbox_vs.Add(self.vbox_vs_slider0, 0, flag=flags)
        
        self.hbox.Add(self.hbox_vs, 0, flag=flags)
        self.hbox.Hide(self.hbox_vs)
        
        self.vbox.Add(self.hbox, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.tb_board_width.SetValue(utils.intervals_to_string(self.board.width))
        self.tb_bit_width.SetValue(utils.intervals_to_string(self.bit.width))
        self.tb_bit_depth.SetValue(utils.intervals_to_string(self.bit.depth))
        self.tb_bit_angle.SetValue('%g' % self.bit.angle)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Layout()
    
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def draw_mpl(self):
        '''
        (Re)draws the matplotlib figure
        '''
        do_spacing = False
        
        old = self.board.width
        str = self.tb_board_width.GetValue()
        self.board.set_width_from_string(str)
        do_spacing = (old != self.board.width)
        
        old = self.bit.width
        str = self.tb_bit_width.GetValue()
        self.bit.set_width_from_string(str)
        do_spacing = do_spacing | (old != self.bit.width)
        
        old = self.bit.depth
        str = self.tb_bit_depth.GetValue()
        self.bit.set_depth_from_string(str)
        do_spacing = do_spacing | (old != self.bit.depth)
        
        old = self.bit.angle
        str = self.tb_bit_angle.GetValue()
        self.bit.set_angle_from_string(str)
        do_spacing = do_spacing | (old != self.bit.angle)

        if do_spacing: self.reinit_spacing()

        self.template = router.Incra_Template(self.board)
        self.mpl.draw(self.template, self.board, self.bit, self.spacing)
        self.canvas.draw()
        self.SendSizeEvent() # bug: not working!
        self.Fit()
    
    def on_cb_es_centered(self, event):
        self.es_cut_values[2] = self.cb_es_centered.GetValue()
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        event.Skip()

    def reinit_spacing(self):
        '''
        Re-initializes the joint spacing objects.  This must be called
        when the router bit or board change dimensions.
        '''
        self.current_spacing = self.combo_spacing.GetStringSelection()

        if self.current_spacing == 'Equal':
            # do the equal spacing parameters.  Preserve the centered option.
            self.equal_spacing = spacing.Equally_Spaced(self.bit, self.board)
            self.equal_spacing_params = self.equal_spacing.get_params()
            p = self.equal_spacing_params[0]
            self.es_slider0.SetRange(p.vMin, p.vMax)
            self.es_slider0.SetValue(p.vInit)
            self.es_cut_values[0] = p.vInit
            p = self.equal_spacing_params[1]
            self.es_slider1.SetRange(p.vMin, p.vMax)
            self.es_slider1.SetValue(p.vInit)
            self.es_cut_values[1] = p.vInit
            p = self.equal_spacing_params[2]
            centered = self.es_cut_values[2]
            self.cb_es_centered.SetValue(centered)
            self.equal_spacing.set_cuts(values=self.es_cut_values)
            self.spacing = self.equal_spacing
            self.hbox.Hide(self.hbox_vs, True)
            self.hbox.Show(self.hbox_es, True)
            # Bug: this hide does not always work
            if self.bit.angle > 0:
                self.hbox_es.Hide(self.cb_es_centered, True)
            else:
                self.hbox_es.Show(self.cb_es_centered, True)
        elif self.current_spacing == 'Variable':
            # do the variable spacing parameters
            self.var_spacing = spacing.Variable_Spaced(self.bit, self.board)
            self.var_spacing_params = self.var_spacing.get_params()
            p = self.var_spacing_params[0]
            self.vs_slider0.SetRange(p.vMin, p.vMax)
            self.vs_slider0.SetValue(p.vInit)
            self.vs_cut_values[0] = p.vInit
            self.var_spacing.set_cuts(values=self.vs_cut_values)
            self.spacing = self.var_spacing
            self.hbox.Hide(self.hbox_es, True)
            self.hbox.Show(self.hbox_vs, True)

        self.Layout()

    def on_combo_spacing(self, event):
        s = self.combo_spacing.GetStringSelection()
        if s != self.current_spacing:
            self.reinit_spacing()
        self.draw_mpl()
        event.Skip()
    
    def on_bit_width(self, event):
        str = self.tb_bit_width.GetValue()
        self.bit.set_width_from_string(str)
        self.reinit_spacing()
        self.draw_mpl()
        event.Skip()
    
    def on_bit_depth(self, event):
        str = self.tb_bit_depth.GetValue()
        self.bit.set_depth_from_string(str)
        self.draw_mpl()
        event.Skip()
    
    def on_bit_angle(self, event):
        str = self.tb_bit_angle.GetValue()
        self.bit.set_angle_from_string(str)
        self.reinit_spacing()
        self.draw_mpl()
        event.Skip()
    
    def on_board_width(self, event):
        str = self.tb_board_width.GetValue()
        self.board.set_width_from_string(str)
        self.reinit_spacing()
        self.draw_mpl()
        event.Skip()
    
    def on_es_slider0(self, event):
        self.es_cut_values[0] = self.es_slider0.GetValue()
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        event.Skip()
    
    def on_es_slider0_key(self, event):
        keycode = event.GetKeyCode()
        print keycode
        if keycode == wx.WXK_SPACE:
            print "you pressed the spacebar!"
        event.Skip()
    
    def on_es_slider1(self, event):
        self.es_cut_values[1] = self.es_slider1.GetValue()
        self.equal_spacing.set_cuts(values=self.es_cut_values)
        self.draw_mpl()
        event.Skip()
    
    def on_vs_slider0(self, event):
        self.vs_cut_values[0] = self.vs_slider0.GetValue()
        self.var_spacing.set_cuts(values=self.vs_cut_values)
        self.draw_mpl()
        event.Skip()
    
    def on_draw_button(self, event):
        self.draw_mpl()
        event.Skip()

    def on_save_plot(self, event):
        # Limit file save types to png and pdf:
        #        file_choices = 'PNG (*.png)|*.png'
        #        file_choices += '|Portable Document File (*.pdf)|*.pdf'
        # Or, these wildcards match what is in the toolbar's save button:
        file_choices = self.canvas._get_imagesave_wildcards()[0]
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="router.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
        event.Skip()
        
    def on_exit(self, event):
        self.Destroy()
        
    def on_about(self, event):
        msg = 'pyRouterJig is a joint layout tool for woodworking.\n\n' +\
              'Copyright 2015 Robert B. Lowrie (pyrouterjig@lowrielodge.org)\n\n' +\
               'pyRouterJig is free software: you can redistribute it and/or modify it under'+\
               ' the terms of the GNU General Public License as published by the Free Software'+\
               ' Foundation, either version 3 of the License, or (at your option) any later'+\
               ' version.\n\n' +\
               'pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY'+\
               ' WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR'+\
               ' A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\n\n'+\
               'You should have received a copy of the GNU General Public License along with'+\
               ' pyRouterJig; see the file COPYING. If not, see http://www.gnu.org/licenses/.\n\n'+\
                   'USE AT YOUR OWN RISK!'
        dlg = wx.MessageDialog(self, msg, 'Welcome to pyRouterJig!', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.timeroff.Bind(wx.EVT_TIMER,  self.on_flash_status_off)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


if __name__ == '__main__':

    # Uncomment this line for metric
    #utils.options.units.metric = True

    app = wx.App(False)
    app.frame = WX_Driver()
    app.frame.Show()
#    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()

