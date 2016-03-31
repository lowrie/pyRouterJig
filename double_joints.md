---
layout: page_doc
title: Documentation
---

<a name="page-index"></a>

This documentation corresponds to version 0.8.9.

This page is split into the following sections ("Return to index" link at the
bottom of each section returns to this location):

* [Wood Pattern Selection](#wood-pattern)
* [Finger Spacing Options](#finger-spacing-options)
* [Editor](#editor)
* [Double and Double-Double Joints](#double)
* [Alignment of Router Passes](#alignment)
* [Drop-Down Menus](#drop-down-menus)
* [Template Details](#incra-template-details)
* [Saving Preferences](#saving-preferences)
* [Needed Improvements](#needed-improvements)
* [Acknowledgments](#acknowledgments)

In addition to the documentation here, I highly recommend [this tutorial put
together by Phil
Barrett.](http://philliplynebarrett.wix.com/philsbunker#!custom-box-joints/f9xbm)
Phil makes beautiful boxes and other wood projects.  He has worthwhile tips
not only for {{ site.codename }}, but also for woodworking and router use in
general.  Take a look at [his
portfolio](http://philliplynebarrett.wix.com/philsbunker#!portfolio/lleih).

<a name="finger-spacing-options"></a>

Finger Spacing Options
======================

Throughout the documentation of {{ site.codename }}, we refer to a \"finger\" not only
as the traditional finger of a box joint, but also generically to refer to a
pin or tail of a dovetail joint.  There are currently two automatic finger-spacing
algorithms, along with an editor to allow specification of arbitrary joints.
The automatic spacing options are <b>Equal</b> and <b>Variable</b>, located at
tabs in the lower-right portion of the window.  Each option has its own
controls, described below:

* <b>Equal:</b> In this case, the fingers are equally spaced.  
  Figures [1](#figure1) and [2](#figure2) are examples.
  There are three inputs that affect this algorithm:

  1. <b>Spacing:</b> This slider allows you to specify additional spacing between
    the A-cuts.  [Figure 4](#figure4) shows an example of increasing this parameter.
  2. <b>Width:</b> This slider allows you to specify additional width added
    to the A-cuts.
    [Figure 5](#figure5) shows an example of increasing this parameter.
  3. <b>Centered:</b> This input is only available for straight bits (bit
    angle = 0).  If this box is checked, a finger is always centered on
    the board.  Otherwise, a full finger is started on the left edge, which
    will result in a centered finger only if the finger width divides into the
    board width an odd number of times.
    [Figure 6](#figure6) shows an example of a non-centered pattern.

  The sliders can be moved by using either dragging the mouse, or my clicking on the
  slider and using the left and right arrow keys for small changes and Page Up
  and Page Down for large changes.

* <b>Variable:</b> In this case a large finger is centered on the board,
  and the fingers decrease in size proportional to the distance to the center.
  There is one input that affects this algorithm:

  1. <b>Fingers:</b> Specifies the approximate number of
    fingers.  At its minimum value, the width of the center finger is maximized. At
    its maximum value, the width of the center finger is minimized, and the result is
    the same as equally-spaced with zero \"Spacing\", zero \"Width\", and
    the \"Centered\" option checked.

[Figure 7](#figure7) shows an example of a Variable-spaced box joint.

<figure>
<a name="figure4"></a>
<img src="{{ site.baseurl }}/images/bspacing_screen_shot.png" alt="Spacing example" data-action="zoom">
<figcaption>
<b>Figure 4.</b>  Effect of Spacing option.  Compared to Fig. 1, the <b>Spacing</b>
slider been moved to a value of 1 17/32".
</figcaption>
</figure>

<figure>
<a name="figure5"></a>
<img src="{{ site.baseurl }}/images/width_screen_shot.png" alt="Width example." data-action="zoom">
<figcaption>
<b>Figure 5.</b>  Effect of Width option.  Compared to Fig. 1, the <b>Width</b>
slider been moved to a value of 27/32".
</figcaption>
</figure>

<figure>
<a name="figure6"></a>
<img src="{{ site.baseurl }}/images/centered_screen_shot.png" alt="Centered example." data-action="zoom">
<figcaption>
<b>Figure 6.</b>  Effect of Centered option.  Compared to Fig. 1, the <b>Board
Width</b> has been changed to 7" and the <b>Centered</b> option unclicked.
</figcaption>
</figure>

<figure>
<a name="figure7"></a>
<img src="{{ site.baseurl }}/images/variable_screen_shot.png" alt="Variable spacing example." data-action="zoom">
<figcaption>
<b>Figure 7.</b>  Variable spacing option.  Compared to Fig. 1, the
<b>Variable</b> tab has been clicked and the <b>Fingers</b> input has a
value of 5.
</figcaption>
</figure>

[Return to index](#page-index)

<a name="editor"></a>

Editor
======

The <b>Editor</b> tab allows you to edit each individual cut of the joint.
The editor operates on the A-cuts of the Top Board; all of the other cuts (B,
C, D, etc.) follow from the A-cuts.  The starting joint for editing is
whatever was last specified under either the <b>Equal</b> or <b>Variable</b>
spacing options.  Under the <b>Editor</b>, the board and bit dimensions, along
with the Double and Double-Double parameters, cannot be changed; make sure
these are set to their final values under either <b>Equal</b> or
<b>Variable</b> before switching to the <b>Editor</b>.

[Figure 8](#figure8) shows an example of entering the <b>Editor</b>, after
setting up the joint as in [Fig. 7](#figure7).  An active cut is highlighted
in red and is the cut which is to be edited, using either the buttons under
the <b>Editor</b> tab, or using keyboard shortcuts.  Again, active cuts are
always on the A-cuts of the Top Board.  The blue outline on a cut indicates
the cut cursor.  The cursor is used to select active cuts.  More than one cut
may be active.  The green vertical lines indicate the extents that the active
cuts can be moved or widened, limited by the bit width.

<figure>
<a name="figure8"></a>
<img src="{{ site.baseurl }}/images/editor_screen_shot.png" alt="Editor example." data-action="zoom">
<figcaption>
<b>Figure 8.</b>  Editor mode, following Variable spacing set up as in Fig. 7.
The first three cuts on the Top Board are active, with the cut cursor on the
center cut.
</figcaption>
</figure>

The Editor functionality is grouped into two main categories, with buttons (or
corresponding keyboard shortcuts) controlling the actions taken.  
The buttons and shortcuts are as follows: 

* <b>Active Cut Select</b>:  This category allows you to select which
  cuts are active.  Active cuts are those for which the <b>Active Cut
  Operators</b> will be applied, described below.
   The buttons for this category are as follows:
  * The arrow buttons (keyboard:  left or right arrows) control the position
  of the cut cursor, shown with a blue outline.  
  * <b>Toggle:</b> (keyboard: `Return`) Toggle the cut at the cursor as active and deactive.
    When active, the cut is highlighted in red.
  * <b>All:</b> (keyboard: `a`) All cuts are set as active.
  * <b>None:</b> (keyboard: `n`) All cuts are set as inactive.
* <b>Active Cut Operators</b>: This category applies editing operators to
  the active cuts, and its buttons are as follows:
  * <b>Move:</b> (keyboard: Hold `Alt` key, along with left and right arrow keys) The arrows move the active cuts 1 increment to the left or right, if possible.
  * <b>Widen:</b> (keyboard: Hold `Shift` key, along with left and right arrow keys) Widens the active cuts on their left or right side by 1 increment, if possible.
  * <b>Trim:</b> (keyboard: Hold `Control` key, along with left or right arrows) Trims the active cuts on their left or right side by 1 increment, if possible.
  * Moves the cut cursor to the right or left
  cut to the right or left to be the active cut.
  * <b>Add:</b>  (keyboard: `+`) Adds one cut, if possible.  There needs to be
    space enough to add a cut, given the board width and bit constraints.  The
    cut is added in the first possible location found, searching from the
    left side of the board.
  * <b>Delete:</b>  (keyboard: `-`) Deletes the active cut.

Finally, the <b>Undo</b> button  (keyboard: `u`) reverses the last editing
operation.  Undo may be applied repeatedly, until the joint is back to the
starting point of invoking the <b>Editor</b>.

Note that if you make changes in the <b>Editor</b>, and then go back to either
<b>Equal</b> or <b>Variable</b> options, the changes will be lost.

[Return to index](#page-index)

<a name="double"></a>

Double and Double-Double Joints
===============================

A Double joint is created simply by selecting a wood pattern other than `NONE`
under <b>Double Board</b>.  Its <b>Thickness</b> may also be changed from
its default of 1/8", similar to parameters such as <b>Board Width</b>.
[Figure 9](#figure9) is an example of a Double joint.

<figure>
<a name="figure9"></a>
<img src="{{ site.baseurl }}/images/double_screen_shot.png" alt="Double joint example." data-action="zoom">
<figcaption>
<b>Figure 9.</b>  Example of a Double joint, following the Equal spacing set up as in Fig. 1.
</figcaption>
</figure>

Once a Double joint has been specified, you can make it a Double-Double joint
by selecting a wood pattern other than `NONE` under <b>Double-Double Board</b>.
[Figure 10](#figure10) is an example of a Double-Double joint.  In this case,
there are two templates which must be aligned in two slots in the INCRA LS
Positioner at the line labeled `ALIGN`.

<figure>
<a name="figure10"></a>
<img src="{{ site.baseurl }}/images/dd_screen_shot.png" alt="Double-double joint example." data-action="zoom">
<figcaption>
<b>Figure 10.</b>  Example of a Double-Double joint, following the the set up as in Fig. 9.
</figcaption>
</figure>

[Return to index](#page-index)

<a name="alignment"></a>

Alignment of Router Passes
==========================

This section discusses how router passes are positioned in general.  For
template alignment, see the section [Template Details](#incra-template-details).

{{ site.codename }} aligns each router pass on equally-spaced \"increments.\"  By default,

* 1 increment = 1/32\" (English units)
* 1 increment = 1 mm (metric units)

An increment is effectively the resolution of {{ site.codename }}.  All dimensions used by
{{ site.codename }}, such as the router-bit width, are rounded to the nearest
number of increments.  The reason for the default choices above is that these
are the resolutions of the respective [INCRA LS Positioner
fence](http://www.incra.com/router_table_fences-ls_positiners.html) (unless
the micro-knob is used).  By using increments, we ensure that it\'s
possible to position the fence at a lock position of the INCRA fence.

If not using an INCRA fence, then you may want to increase the resolution.
This may be accomplished through the <b>Increments per inch</b> (or per mm) parameter in the
<b>Preferences</b>; see the section [Saving Preferences](#saving-preferences).

[Return to index](#page-index)

<a name="drop-down-menus"></a>

Drop-Down Menus
===============

Drop-down menus are located at the top of the application window, except for
the Mac, where menus are placed in the menubar at the top of the screen.
There are four menus available (on the Mac, five menus, with some items noted
below under the <b>pyRouterJig</b> menu):

1. <b>File:</b>
* <b>Open (Ctrl-O)</b> Opens a previously saved or screenshot file (see
<b>Save</b> and <b>Screenshot</b>).
{{ site.codename }} embeds the joint data in the `PNG` image files that it
saves.  Opening the `PNG` file will allow you to start work again where you
left off.  Note that in the <b>Editor</b> mode, the Undo history is
not saved.   Any of the images in this documentation page may be opened with
{{ site.codename }}.  For the wood images described in [Wood Pattern
Selection](#wood-pattern), only the name of the wood image is saved.  So
if the image uses wood images, such as the `hard-maple` and `black-walnut` in
[Figure 9](#figure9),  if you don't have these images available
in your own `wood_images` folder, then a simple pattern is substituted.
* <b>Save (Ctrl-S)</b> Saves the joint figure as a `PNG` file.  By
default, the image files are placed in your home directory, numbered sequentially as
`pyrouterjig_0.png`, `pyrouterjig_1.png`, `pyrouterjig_2.png`, and so on.  The
image size is the same as your current window size, but no smaller than
`Min Image Width` and no bigger than `Max Image Width`, both of which 
may be set under <b>Preferences</b>.  By default, both are
set to `1440`, meaning that all saved images are of this width.
[Figure 11](#figure11) shows the saved image corresponding to [Figure 10](#figure10).
* <b>Print (Ctrl-P)</b> Allows you to print the joint diagram (including print
to a file). {{ site.codename }} prints through a preview screen.  Press the printer icon
at the upper-right of the preview screen to either select the printer, or to
print to a file.
* <b>Quit (Ctrl-Q)</b> Quits {{ site.codename}} (on Mac, located under the <b>pyRouterJig</b> menu).  If you\'ve made any changes
to the joint and haven\'t saved it, then you\'ll be warned.
1. <b>View:</b>
* <b>Fullscreen (Ctrl-F)</b> Toggles full-screen mode.
* <b>Caul Template</b> <a name="view-caul-template"></a>
Toggles the caul template (default may be set under <b>Preferences</b>). The caul template is an
additional template that can be used to create clamping cauls for the
joint with the INCRA LS Positioner.  It's assumed that a straight router bit of the
same width is used to create the cauls.  The template follows the same pattern as that for the
Top and Bottom Boards, but with narrower fingers.  By default, 1
increment is removed from the side of each finger. [Figure 12](#figure12)
shows an example of the caul template.  Phil Barrett also has a [very nice
tutorial on clamping cauls using {{ site.codename }}](http://philliplynebarrett.wix.com/philsbunker#!creating-box-joint-cauls/q2r7v).
* <b>Finger Widths</b> Toggles whether the finger widths are displayed on
each finger of each board.
* <b>Router Passes</b>  <a name="view-router-passes"></a>Options under this menu control if and how router
passes are drawn on each board.  If all options are unchecked, then no router
passes are drawn.  The values are:
  * <b>Identifiers</b> Toggles whether the pass identifier is included in the label.
  * <b>Locations</b> Toggles whether the pass location is included in the
  label.  The location is measured from the right side of the board.  By
  aligning the Incra ruler to the right side of the board, the locations may
  be used to double-check the alignment of each router pass.  This can be
  useful if your printer is not very accurate.
1. <b>Tools:</b>
* <b>Screenshot (Ctrl-W)</b> Similar to <b>Save</b>, but includes the entire
{{ site.codename }} application window.  The image size is the same as your
current window size.  Figures 1 through 10 were created with
<b>Screenshot</b>.  Screenshots always use the default filename for output and
are meant to be used to quickly generate image files (such as for this documentation!).
* <b>Export 3DS (Ctrl-E)</b> Allows you to export certain joints to a 3DS
file.  A 3DS file may be imported into SketchUp.  This feature is under
development and currently unavailable for dovetail bits, Double joints, and
Double-Double joints.
* <b>Preferences (Ctrl-,)</b> Opens the Preferences window (on Mac, located under the <b>pyRouterJig</b> menu).
1. <b>Help:</b>
* <b>About (Ctrl-A)</b> Pops up a window showing the version and license (on Mac, located under the <b>pyRouterJig</b> menu).
* <b>Documentation</b> Opens your default browser and goes to the
documentation page you are now reading.  You must have an Internet connection for
this operation to work.

On the Mac, for the keyboard shortcuts use the `Command` key rather than `Ctrl`.

<figure>
<a name="figure11"></a>
<img src="{{ site.baseurl }}/images/dd_fig.png" alt="Save option figure." data-action="zoom">
<figcaption>
<b>Figure 11.</b> The same as Figure 10, but using <b>Save</b> rather than
<b>Screenshot</b> to create the image file.
</figcaption>
</figure>

<figure>
<a name="figure12"></a>
<img src="{{ site.baseurl }}/images/caul_screen_shot.png" alt="Example of Caul Template." data-action="zoom">
<figcaption>
<b>Figure 12.</b> The same as Figure 1, but after toggling <b>Caul
Template</b> under the <b>View</b> menu.  The A-cuts on the Cauls template
will create a clamping caul for the Top Board, while the B-cuts create a
clamping caul for the Bottom Board.
</figcaption>
</figure>

[Return to index](#page-index)

<a name="incra-template-details"></a>

Template Details
================

As mentioned above, the template may be cut out and used in a INCRA LS
Positioner fence.  Referring to any of the figures above, the template needs
some explanation:

* The router passes are labeled with their ordering and the edge letter (A, B,
  C, etc.).
* The gray regions are margins for the template, outside the board\'s width.
  It\'s possible for a pass to be placed in the gray region, if the outer
  fingers are narrower than half of the <b>Bit Width</b>.
* A template may be aligned in one of two ways:
  1. Using the centerline of the template and the procedure explained in the
  INCRA manual.  For each template, either the centerline is shown as a dashed
  line that spans the template height, or if the centerline coincides with a
  cut, that cut denoted on each end of the template.  For example, in [Figure
  11](#figure11), the bottom template indicates that the centerline coincides with
  cut `3E`, whereas the top template draws the centerline between cuts `5C`
  and `6C`.
  1. The `ALIGN` line is located 1/2 the bit width on the outside of the right
  edge of the board.  Therefore, if you align your bit flush with the fence and
  then position the template at the `ALIGN` line, your template will be
  properly positioned.
* On any one router pass, a good rule of thumb is not to cut deeper than the
  <b>Bit Width</b>.  So for example, for a <b>Bit Width</b> of 1/2" and a
  <b>Bit Depth</b> of 3/4", it's best to run the board through twice, the
  first pass with the depth set at 3/8", and the second pass at 3/4".  This
  rule of thumb may vary with the particular wood species, the sharpness of your
  bit, minimizing tear-out, and other variables.
* It\'s important that your printer not distort the template when
  printing the template on paper.  I have a cheap inkjet printer that
  often distorts the template about 1/32" over 4".  This is well
  outside the accuracy of an INCRA fence. If the print scaling appears
  consistent across the page, you might try
  changing the parameter `Print Scale Factor` in the <b>Preferences</b>.
  But if all else fails, try the following steps:
  1. Toggle the menu item <b>View : Router Passes : Locations</b> to turn on the location of
  each router pass. The locations are with respect to the right edge of the
  board.
  1. Align INCRA's metal ruler with the board's right edge.
  On the template, the right edge is located at the edge of the right,
  gray-shaded region. Ideally, you can locate
  the ruler so that its zero value is at the right edge, but this may push the
  ruler outside its channel.  You really just need a reference value that you
  can easily add to the router pass locations displayed in Step 1.
  1. For each pass, the template will get you close.  But you can also use the
  ruler to double check that the fence is at the precise location.


[Return to index](#page-index)

<a name="saving-preferences"></a>

Saving Preferences
==================

Certain settings may be made and saved permanently under the
<b>Preferences</b> window, so that they are the default setting when you run
{{ site.codename }} again in the future.  The <b>Preferences</b> window may be
opened by selecting the menu item <b>Tools : Preferences</b> (on Mac,
<b>pyRouterJig : Preferences</b>), or `Ctrl-,`, and appears as below.

<img src="{{ site.baseurl }}/images/prefs_window.png" alt="Preferences window">

The individual preferences are organized under tabs.  At the bottom of the
<b>Preferences</b> window are the <b>Cancel</b> and <b>Save</b> buttons.  The
<b>Cancel</b> button discards any changes that you have made under the
<b>Preferences</b> window and returns to the main application window.  The
<b>Save</b> button saves preference changes permanently and is active only if
settings have been changed (it's inactive in the image above).

Each tab and its preferences are as follows:

* <b>Output:</b> This tab contains preferences that control output appearance
for the main application window, for printing, and for saving images.
  * <b>Show Caul Template:</b> If checked, the clamping caul template is
  displayed.  This option may be also set under the menu <b>View : Caul
  Template</b>; [see its documentation](#view-caul-template) for more information.
  * <b>Show Finger Widths:</b> If checked, each finger is labeled with its width.
  This option may be also set under the menu <b>View : Finger Widths</b>.
  * <b>Show Router Pass Identifiers:</b> If checked, each router pass is
  labeled with its router pass identifier.
  This option may be also set under the menu <b>View : Router Passes :
  Identifiers</b>;  [see its documentation](#view-router-passes) for more information.
  * <b>Show Router Pass Locations:</b> If checked, each router pass is labeled
  with its distance from the right edge.
  This option may be also set under the menu <b>View : Router Passes :
  Locations</b> ;  [see its documentation](#view-router-passes) for more information.
* <b>Boards:</b> This tab contains preferences related to the Boards.  The
only parameter here that needs explanation is the <b>Wood Images Folder</b>,
which is the directory where wood image files are located.  See the section
[Wood Pattern Selection](#wood-pattern) for more information.
* <b>Bit:</b> This tab contains preferences related to the Bits and are self explanatory.
* <b>Units:</b> This tab allows you to change the unit system.  Note that any
changes under this tab, if saved, will require {{ site.codename }} to
restart, and you will loose any unsaved work that you have done on the current
joint.  A setting here is <b>Increments per [inch|mm]</b>, which
is an advanced setting described in the section [Alignment of Router
Passes](#alignment).  Do not change this value if you plan to use the
templates with the Incra LS Positioner.
* <b>Misc:</b> Two parameters may be set under this tab:
  * <b>Min Finger Width:</b>  This is the minimum allowable finger width.
  Currently, this value is enforced only for the <b>Equal</b> spacing
  algorithm.
  * <b>Caul Trim:</b>  This value is used to determine the width of each
  clamping caul finger.  It's the distance from the edge of each
  board finger to the edge its corresponding caul finger.  In other words,
  the caul fingers are narrower than the board fingers by twice this value.

Note that some settings may be changed outside the <b>Preferences</b> window.  For
example, the setting <b>Output : Show Finger Widths</b> may also be
set under the menu <b>View : Finger Widths</b>.  These settings are made
permanent by opening the <b>Preferences</b> window and pressing the
<b>Save</b> button.

The preferences are saved in the configuration file `.pyrouterjig`, created
in the user's home directory when {{ site.codename }} is first executed.
Specifically,

* Windows: `C:\users\<your name>\.pyrouterjig`
* Mac: `/Users/<login name>/.pyrouterjig`.  Note that this is a "hidden" file
on the Mac and so, for example, it won't show up in the Finder without changing Finder's
settings.  Google `hidden files mac` if you don't know how to access hidden files.

This file contains the preferences, along with a few additional options, each
described within the file itself.  Setting these options requires a basic
knowledge of Python.  If you change the configuration file while 
{{ site.codename }} is running, the options will not take effect until you quit
and restart {{ site.codename }}.

When upgrading to a newer version of {{ site.codename }}, it may be required
to update your `.pyrouterjig` file.  {{ site.codename }} will attempt to
migrate settings.  If unable to migrate settings, default settings are used.
Regardless, your old `.pyrouterjig` is moved to `.pyrouterjigX.X.X`,
where `X.X.X` is the code version that created the file.

[Return to index](#page-index)

<a name="needed-improvements"></a>

Needed Improvements
===================

I am looking for help to make the improvements outlined in this section.  I
will certainly give credit to those who help make these or any other
improvements.  If you\'re thinking of contributing, let me know, because I may
have already started on some of these issues.

* <b>Windows and Linux Support.</b>  If you can help test and improve {{ site.codename }} on
any platform, particularly Windows and Linux, please contact me.
* <b>Upgrade Python and Qt.</b>  Once anaconda supports PyQt5, I plan to
upgrade to both Python 3.5 and PyQt5.
* <b>Known Bugs.</b>
  * In Print Preview mode, the board fill patterns often look very
  strange.  [This link at Qt](https://bugreports.qt.io/browse/QTBUG-30260) describes
  what appears to be the same bug.  Once the folks at Qt fix this issue, I'll
  release a new version.  Note that the actual printout should look fine; it's
  the Preview that looks strange.
* <b>Features.</b> I\'m working on or considering the following features:
  * In Editor mode, allow for certain changes in parameters, such as board width
  and bit width.  The reason changes are disabled now is that parameter changes
  may create errors that are difficult to recover from.
  * Specification of color schemes.
  * Export to Sketchup, or a file that it can import.  This is underway, via
  `Export 3DS`, but not all joints are supported yet.
  * Define an option for \"fold-over templates\" that are appropriate for
    laying out hand-cut joints.
  * More spacing options.
  * Cleaning up these web pages. Create a web page with more example joints.

[Return to index](#page-index)

<a name="acknowledgments"></a>

Acknowledgments
===============

Special thanks to the following individuals:

* Phil Barrett for his numerous suggestions for improvement and testing help.
I'm always amazed at the bugs he finds.  Among many great ideas, in particular
he should be credited with the ideas of storing the joint metadata in the
`PNG` file, the clamping caul template, and the easy template alignment method.  He
also tests on Windows 10.  Finally, he put together [this great tutorial](http://philliplynebarrett.wix.com/philsbunker#!custom-box-joints/f9xbm)
of {{ site.codename }}.
* George Salek for testing (particularly on Windows XP), finding bugs and
issues with metric units.

{{ site.codename }} depends upon and is extremely grateful for the following
open-source software efforts:

* [Python](http://www.python.org)
* [PyQt](http://sourceforge.net/projects/pyqt/)
* [PyInstaller](http://www.pyinstaller.org/)
* [Anaconda](https://www.continuum.io/)

[Return to index](#page-index)
