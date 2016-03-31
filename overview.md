---
layout: page_doc
title: Overview
---

When you start {{ site.codename }}, it will prompt you for the units you would
like to work in, as shown below:

<img src="{{ site.baseurl }}/images/select_units.png" alt="Select units window">

Your choice of unit system will be saved in a configuration file, which is
described in the section [Saving Preferences](#saving-preferences), and you
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
Each finger is labeled with its width.

Below the boards is the corresponding template that may be
cut out and used in an INCRA LS Positioner. See [Template
Details](#incra-template-details) for more details on the templates.  Below the template is a concise
title that summarizes the properties of the joint.  The graphics containing the boards,
template, and title may be printed by selecting <b>Print</b> in the
<b>File</b> pull-down menu, or by pressing the key combination `Ctrl-P`
(`Command-P` on Mac).

The lower part of the window allows you to change interactively the parameters
for the joint.  The joint is re-drawn after each change.  At the lower left,
you can see two rows of input parameters, which are available for any
finger-spacing algorithm.  On the top row, we have

* <b>Board Width [inches|mm]:</b> The board width of the joint.
* <b>Bit Width [inches|mm]:</b>  The maximum cutting width of the router bit.
* <b>Bit Depth [inches|mm]:</b> The cutting depth of the router bit.
* <b>Bit Angle [degrees]:</b> The angle of the router bit.  Zero indicates
  a straight bit (box joint).

These parameters are changed by entering text for the dimension in their
respective text boxes, shown in the image above.  Moving the cursor outside
the text box, or hitting the Enter key, will automatically update the value
and redraw the joint with the new value.  For English units, the length
values are in inches, while for metric, the values are in millimeters (mm).
The values may be specified as either a fraction or decimal.
For example, the following are equivalent:

* `7 1/2`
* `7.5`
* `7 1 / 2`
* `7 1 /2`
* `7 1/ 2`

Note that the whitespace around the \"`/`\" is ignored.

The values with length dimension (inches or mm) are rounded to the nearest
alignment point.  By default for English units, values are rounded to the nearest
1/32\".  By default for metric, values are rounded to the  nearest
millimeter.  See section [Alignment of Router Passes](#alignment) for more
information about alignment.

To create a dovetail joint, change <b>Bit Angle</b> to 7 degrees, and we obtain the
dovetail joint shown in [Figure 2](#figure2) below:

<figure class="zoomable">
<a name="figure2">
<img src="{{ site.baseurl }}/images/dovetail_screen_shot.png">
</a>
<figcaption>
<b>Figure 2.</b>  Dovetail example.  Compared to Fig. 1, the <b>Bit Angle</b>
has been changed to 7 degrees.
</figcaption>
</figure>

<div id="textbox">
  <p class="alignright">
    <a href="{{ site.baseurl }}/wood_patterns/">Next: Wood Pattern Selection</a>
  </p>
</div>
<div style="clear: both;"></div>
