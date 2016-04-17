---
layout: page_doc
title: Dovetail Specifics
---

Several issues have to kept in mind when laying out dovetails, particularly
for the Incra LS Positioner.  Because the Incra limits the fence position to
`1/32"` increments (`1 mm` for metric), a given bit and depth setting will
typically create a small *gap* or *overlap*.  Any overlap should be avoided,
as then the joint will be an interference fit.

A good example is to set <b>Bit Width</b> to `3/8`, <b>Bit Depth</b> to `1/4`,
and <b>Bit Angle</b> to `9`, as shown in Figure 13 below:
<figure class="zoomable">
<a name="figure13">
<img src="{{ site.baseurl }}/images/fit_overlap_screen_shot.png">
<a data-featherlight="{{ site.baseurl }}/images/fit_overlap_zoom.png">
<img src="{{ site.baseurl }}/images/fit_overlap_zoom.png">
</a>
</a>
<figcaption>
<b>Figure 13.</b> Dovetail joint that has an overlap of 0.008".
Bottom image shows joint detail.
</figcaption>
</figure>
In order to see the fit better, through the menus, we've also toggled off
<b>View : Finger Widths</b> and <b>View : Router Passes : Identifiers</b>,
and toggled on <b>View : Fit</b>.  We also set <b>Top Board</b> and <b>Bottom Board</b>
to `Solid Fill`.  The red warning banner at the lower left of the window
indicates that the joint's maximum overlap of `0.008"` exceeds the value <b>Warning
overlap</b>, which defaults to `0"` and 
may be [set in the Preferences under the <b>Misc</b> tab]({{ site.baseurl }}/saving_preferences/).

By changing the <b>Bit Depth</b> to `3/16"` results in a gap of `0.002"`,
which is shown in Fig. 14 below:
<figure class="zoomable">
<a name="figure14">
<img src="{{ site.baseurl }}/images/fit_gap_screen_shot.png">
<a data-featherlight="{{ site.baseurl }}/images/fit_gap_zoom.png">
<img src="{{ site.baseurl }}/images/fit_gap_zoom.png">
</a>
</a>
<figcaption>
<b>Figure 14.</b> Dovetail joint that has an overlap of 0.002".
Compared to Fig. 13, the bit depth was changed to `3/16`.
</figcaption>
</figure>
This gap does not exceed the value <b>Warning gap</b>, which defaults to
`0.005"`, and so the lower-left banner remains green text.

Now, if we set the <b>Bit Depth</b> to `0.197"`, we get no overlap or gap, as
shown in Fig. 15 below:
<figure class="zoomable">
<a name="figure15">
<img src="{{ site.baseurl }}/images/fit_perfect_screen_shot.png">
<a data-featherlight="{{ site.baseurl }}/images/fit_perfect_zoom.png">
<img src="{{ site.baseurl }}/images/fit_perfect_zoom.png">
</a>
</a>
<figcaption>
<b>Figure 15.</b> Dovetail joint that has no overlap or gap.
Compared to Fig. 13, the bit depth was changed to `0.197`.
</figcaption>
</figure>

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/template/">Prev: Template Details</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/saving_preferences/">Next: Saving Preferences</a>
  </p>
</div>
<div style="clear: both;"></div>
