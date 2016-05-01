---
layout: page_doc
title: Drop-down menus
---

Drop-down menus are located at the top of the application window, except for
the Mac, where menus are placed in the menubar at the top of the screen.
There are four menus available (on the Mac, five menus, with some items noted
below under the {{ site.codename }} menu), described below.
Note that on the Mac, the keyboard shortcuts use the `Command` key rather than `Ctrl`.

1. <b>File:</b>
*  <b>Open (`Ctrl-O`)</b> Opens a previously saved or screenshot file (see
   <b>Save</b> and <b>Screenshot</b>).
   {{ site.codename }} embeds the joint data in the `PNG` image files that it
   saves.  Opening the `PNG` file will allow you to start work again where you
   left off.  Note that in the <b>Editor</b> mode, the Undo history is
   not saved.   Any of the images in this documentation page may be opened with
   {{ site.codename }}.  For the wood images described in the
   <a href="{{ site.baseurl }}/wood_patterns/">section Wood Pattern Selection</a>,
   only the name of the wood image is saved.  So
   if the image uses wood images, such as the `black-walnut` and `mahogany` in
   <a data-featherlight="{{ site.baseurl }}/images/dd_screen_shot.png">this
   example</a>,  and those images are not found
   in your own `wood_images` folder, then a simple pattern is substituted.
*  <b>Save (`Ctrl-S`)</b> Saves the joint figure as a `PNG` file.  By
   default, the image files are placed in your home directory, numbered sequentially as
   `pyrouterjig0.png`, `pyrouterjig1.png`, `pyrouterjig2.png`, and so on.  The
   image size is the same as your current window size, but no smaller than
   `Min Image Width` and no bigger than `Max Image Width`, both of which 
   may be set under <b>Preferences</b>.  By default, both are
   set to `1440`, meaning that all saved images are of this width.
   [Figure 11](#figure11) shows an example saved image.
   <figure class="zoomable">
   <a name="figure11">
   <img src="{{ site.baseurl }}/images/dd_fig.png">
   </a>
   <figcaption>
   <b>Figure 11.</b> The same case as
   <a data-featherlight="{{ site.baseurl }}/images/dd_screen_shot.png">this
   example</a>, but using <b>Save</b> rather than
   <b>Screenshot</b> to create the image file.
   </figcaption>
   </figure>
*  <b>Print (`Ctrl-P`)</b> Allows you to print the joint diagram (including print
   to a file). {{ site.codename }} prints through a preview screen.  Press the printer icon
   at the upper-right of the preview screen to either select the printer, or to
   print to a file.
*  <b>Quit (`Ctrl-Q`)</b> Quits {{ site.codename}} (on Mac, located under the <b>pyRouterJig</b> menu).  If you\'ve made any changes
   to the joint and haven\'t saved it, then you\'ll be warned.
1. <b>View:</b>
*  <b>Caul Template</b> <a name="view-caul-template"></a>
   Toggles the caul template (default may be set under <b>Preferences</b>). The caul template is an
   additional template that can be used to create clamping cauls for the
   joint with the INCRA LS Positioner.  It's assumed that a straight router bit of the
   same width is used to create the cauls.  The template follows the same pattern as that for the
   Top and Bottom Boards, but with narrower fingers.  By default, 1
   increment is removed from the side of each finger. [Figure 12](#figure12)
   shows an example of the caul template.  Phil Barrett also has a [very nice
   tutorial on clamping cauls using {{ site.codename }}](http://philliplynebarrett.wix.com/philsbunker#!creating-box-joint-cauls/q2r7v).
   <figure class="zoomable">
   <a name="figure12">
   <img src="{{ site.baseurl }}/images/caul_screen_shot.png">
   </a>
   <figcaption>
   <b>Figure 12.</b> The same as 
   <a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
   opening screenshot</a>, but after toggling <b>Caul
   Template</b> under the <b>View</b> menu.  The A-cuts on the Cauls template
   will create a clamping caul for the Top Board, while the B-cuts create a
   clamping caul for the Bottom Board.
   </figcaption>
   </figure>
*  <b>Finger Widths</b> Toggles whether the finger widths are displayed on
   each finger of each board.
*  <b>Fit</b> Toggles a view of the joint assembled.  By "assembled", we mean
a flattened, two-dimensional view.  This view is useful for checking the fit
of dovetail joints, which because of the Incra's positioning at discrete
increments, can result in a small amount of overlap in the fit.
*  <b>Router Passes</b>  <a name="view-router-passes"></a>Options under this menu control if and how router
   passes are drawn on each board.  If all options are unchecked, then no router
   passes are drawn.  The values are:
  *  <b>Identifiers</b> Toggles whether the pass identifier is included in the label.
  *  <b>Locations</b> Toggles whether the pass location is included in the
     label.  The location is measured from the right side of the board.  By
     aligning the Incra ruler to the right side of the board, the locations may
     be used to double-check the alignment of each router pass.  This can be
     useful if your printer is not very accurate.
*  <b>Full Screen Mode (`Ctrl-F`)</b> Toggles full-screen mode.  On the Mac,
the operating system adds an additional menu item called <b>Enter Full Screen</b>,
which is buggy.  Use <b>Full Screen Mode</b> instead.
1. <b>Tools:</b>
*  <b>Screenshot (`Ctrl-W`)</b> Similar to <b>Save</b>, but includes the entire
   {{ site.codename }} application window.  The image size is the same as your
   current window size.  <a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">
   The opening screenshot image</a> was created with
   <b>Screenshot</b>.  Screenshots always use the default filename for output and
   are meant to be used to quickly generate image files (such as for this documentation!).
*  <b>Export 3DS (`Ctrl-E`)</b> Allows you to export certain joints to a 3DS
   file.  A 3DS file may be imported into SketchUp.  This feature is under
   development and currently unavailable for dovetail bits, Double joints, and
   Double-Double joints.
*  <b>Preferences (`Ctrl-,`)</b> Opens the Preferences window (on Mac, located under the <b>pyRouterJig</b> menu).
1. <b>Help:</b>
*  <b>About (`Ctrl-A`)</b> Pops up a window showing the version and license (on Mac, located under the <b>pyRouterJig</b> menu).
*  <b>Documentation</b> Opens your default browser and goes to the
   documentation page you are now reading.  You must have an Internet connection for
   this operation to work.

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/alignment/">Prev: Alignment of Router Passes</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/template/">Next: Template Details</a>
  </p>
</div>
<div style="clear: both;"></div>
