---
layout: page_doc
title: Saving Preferences
---

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

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/template/">Prev: Template Details</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/needed_improvements/">Next: Needed Improvements</a>
  </p>
</div>
<div style="clear: both;"></div>
