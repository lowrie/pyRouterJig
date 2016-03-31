---
layout: page_doc
title: Wood Pattern Selection
---

On the bottom row of the lower-left input parameters are <b>Top Board</b>,
<b>Bottom Board</b>, <b>Double Board</b>, and <b>Double-Double Board</b>,
which allow you to select the pattern or wood images used to draw these
boards, along with parameters for Double and Double-Double joints.  The Double
and Double-Double joints are explained in the 
<a href="{{ site.baseurl }}/double_joints/">section Double Joints</a>.
In this section, we cover how to specify
patterns for any board and how to add image files to simulate
the appearance of wood grain.

The patterns for Boards may be selected under each respective board header
(Top, Bottom, Double, and Double-Double).  By default, {{ site.codename }}
uses simple patterns to draw the board, such as the default `DiagCrossPattern`
shown in the figures above.  You may also specify any image file (such as a
Portable Network Graphics - PNG) to draw the board.  At startup, 
{{ site.codename }} looks in the `wood_images` folder in your home directory
and assumes any file in this folder is an image file.  It then makes these
images available to draw any of the boards.  The name and location of the
folder may be changed under the <b>Preferences</b> window; see the section
<a href="{{ site.baseurl }}/saving_preferences/">Saving Preferences</a>.

A starting `wood_images` can be downloaded [from this link]({{ site.baseurl }}/wood_images.zip).
Unzip this file in your home directory and you should be
ready to go.  As an example, the file `hard-maple.png` is in this `wood_images` folder.
Using this image for the Top and Bottom Boards in 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the opening screenshot</a>
displays [Figure 3](#figure3).
Other wood image files can be obtained from [the wood database
website](http://www.wood-database.com/).

<figure class="zoomable">
<a name="figure3">
<img src="{{ site.baseurl }}/images/woods_screen_shot.png">
</a>
<figcaption>
<b>Figure 3.</b>  Same as <a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, but using a "hard-maple" image file for
the Top and Bottom Boards.
</figcaption>
</figure>

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/overview/">Prev: Overview</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/finger_spacing_options/">Next: Finger Spacing Options</a>
  </p>
</div>
<div style="clear: both;"></div>
