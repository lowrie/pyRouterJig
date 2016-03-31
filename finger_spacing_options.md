---
layout: page_doc
title: Finger Spacing Options
---

Throughout the documentation of {{ site.codename }}, we refer to a \"finger\" not only
as the traditional finger of a box joint, but also generically to refer to a
pin or tail of a dovetail joint.  There are currently two automatic finger-spacing
algorithms, along with an editor to allow specification of arbitrary joints.
The automatic spacing options are <b>Equal</b> and <b>Variable</b>, located at
tabs in the lower-right portion of the window.  Each option has its own
controls, described below:


* <a name="equal_spacing"></a>
  <b>Equal:</b> In this case, the fingers are equally spaced.  
  <a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">The
  opening screenshot</a> is an example.
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

<figure class="zoomable">
<a name="figure4">
<img src="{{ site.baseurl }}/images/bspacing_screen_shot.png">
</a>
<figcaption>
<b>Figure 4.</b>  Effect of Spacing option.  Compared to 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, the <b>Spacing</b>
slider been moved to a value of 1 17/32".
</figcaption>
</figure>

<figure class="zoomable">
<a name="figure5">
<img src="{{ site.baseurl }}/images/width_screen_shot.png">
</a>
<figcaption>
<b>Figure 5.</b>  Effect of Width option.  Compared to 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, the <b>Width</b>
slider been moved to a value of 27/32".
</figcaption>
</figure>

<figure class="zoomable">
<a name="figure6">
<img src="{{ site.baseurl }}/images/centered_screen_shot.png">
</a>
<figcaption>
<b>Figure 6.</b>  Effect of Centered option.  Compared to 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, the <b>Board
Width</b> has been changed to 7" and the <b>Centered</b> option unclicked.
</figcaption>
</figure>


* <a name="variable_spacing"></a>
  <b>Variable:</b> In this case a large finger is centered on the board,
  and the fingers decrease in size proportional to the distance to the center.
  There is one input that affects this algorithm:

  1. <b>Fingers:</b> Specifies the approximate number of
    fingers.  At its minimum value, the width of the center finger is maximized. At
    its maximum value, the width of the center finger is minimized, and the result is
    the same as equally-spaced with zero \"Spacing\", zero \"Width\", and
    the \"Centered\" option checked.

  [Figure 7](#figure7) shows an example of a Variable-spaced box joint.

<figure class="zoomable">
<a name="figure7">
<img src="{{ site.baseurl }}/images/variable_screen_shot.png">
</a>
<figcaption>
<b>Figure 7.</b>  Variable spacing option.  Compared to 
<a data-featherlight="{{ site.baseurl }}/images/opening_screen_shot.png">the
opening screenshot</a>, the
<b>Variable</b> tab has been clicked and the <b>Fingers</b> input has a
value of 5.
</figcaption>
</figure>

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/wood_patterns/">Prev: Wood Pattern Selection</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/editor/">Next: Editor</a>
  </p>
</div>
<div style="clear: both;"></div>
