---
layout: page_doc
title: Overview
---

When you start {{ site.codename }}, it will prompt you for the units you would
like to work in, as shown in the right window.
<img class="floater" src="{{ site.baseurl }}/images/select_units.png" 
     alt="Select units window" width="512">
Your choice of unit system will be saved in a configuration file, which is
described in the <a href="{{ site.baseurl }}/saving_preferences/">section Saving Preferences</a>, and you
will not be asked again.

After selecting the units, a new window is created, and you should see something like the image
below (this image is from a Windows platform; on other platforms,
the image may differ):

<figure class="zoomable">
<a name="figure1">
<img src="{{ site.baseurl }}/images/opening_screen_shot.png">
</a>
<figcaption>
<b>Figure 1.</b>  Opening screenshot, English units.  Using metric units, the
opening screenshot is similar.
</figcaption>
</figure>

This documentation is focused on using English units, but any important
differences will be discussed compared with metric units.
The default joint is a box joint, with the fingers equally spaced, over a
width of 7 1/2\".  The upper portion of the window draws the current joint.

Below the boards is the corresponding template that may be
cut out and used in an INCRA LS Positioner. See 
<a href="{{ site.baseurl }}/template/">Template Details</a>
for more details on the templates.  Below the template is a concise
title that summarizes the properties of the joint.  The graphics containing the boards,
template, and title may be printed by selecting <b>Print</b> in the
<b>File</b> pull-down menu, or by pressing the key combination `Ctrl-P`
(`Command-P` on Mac).

The lower part of the window allows you to change interactively the parameters
for the joint.  The joint is re-drawn after each change.  In the lower-left grid,
<img class="floater" src="{{ site.baseurl }}/images/lower_left.png" 
     alt="Select units window" width="512">
you can see two rows of input parameters, which are available for any
finger-pattern algorithm.  On the top row, we have

* <b>Board Width [inches|mm]:</b> The board width of the joint.
* <b>Bit Width [inches|mm]:</b>  The maximum cutting width of the router bit.
* <b>Bit Depth [inches|mm]:</b> The cutting depth of the router bit.
* <b>Bit Angle [degrees]:</b> The angle of the router bit.  Zero indicates
  a straight bit (box joint).

These parameters are changed by entering text for the dimension in their
respective text boxes, shown in the image above.  Moving the cursor outside
the text box, or hitting the Enter key, will automatically update the value
and redraw the joint with the new value.  The values may be specified as
either a fraction or decimal.  For example, the following are equivalent:

`7 1/2` or `7.5` or `7 1 / 2` or `7 1 /2` or `7 1/ 2`

Note that the whitespace around the \"`/`\" is ignored. The board and bit
widths are rounded to the nearest alignment point.  By default, alignment is
every 1/32\" (or 1 mm for metric).  See section <a href="{{
site.baseurl }}/alignment/">Alignment of Router Passes</a> for more
information about alignment.

On the bottom row of the lower-left grid parameters are <b>Top Board</b>,
<b>Bottom Board</b>, <b>Double Board</b>, and <b>Double-Double Board</b>,
which allow you to select the pattern or wood images used to draw these
boards, along with parameters for Double and Double-Double joints.
See the sections [Wood Pattern Selection]({{ site.baseurl }}/wood_patterns/)
and [Double Joints]({{ site.baseurl }}/double_joints/) for more information.

To create a dovetail joint, change <b>Bit Angle</b> to 7 degrees, and we obtain the
dovetail joint shown in [Figure 2](#figure2) below:

<figure class="zoomable">
<a name="figure2">
<img src="{{ site.baseurl }}/images/dovetail_screen_shot.png">
</a>
<figcaption>
<b>Figure 2.</b>  Dovetail example.  Compared to 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, the <b>Bit Angle</b>
has been changed to 7 degrees.
</figcaption>
</figure>

On the bottom right of the window various finger pattern options are
available.  See the section [Finger Pattern Options]({{ site.baseurl
}}/finger_spacing_options/) for information about <b>Equal</b> and
<b>Variable</b>.  The <b>Editor</b> always you to customize the finger
patterns even further and is described in the section [Editor]({{ site.baseurl
}}/editor/).  Below the finger pattern options is the template watermark text box,
which may be used to label the template.

<div id="textbox">
  <p class="alignright">
    <a href="{{ site.baseurl }}/wood_patterns/">Next: Wood Pattern Selection</a>
  </p>
</div>
<div style="clear: both;"></div>
