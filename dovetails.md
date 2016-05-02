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
<b>View : Router Passes : Identifiers</b>
and toggled on <b>View : Fit</b>.  For the zoomed images, we also changed the `Alpha Channel` in the
`Board Background` color preference to a value of 100, which makes the boards
semi-transparent, so that any overlap is
easily viewed.  The red warning banner at the lower left of the window
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
<b>Figure 14.</b> Dovetail joint that has an gap of 0.002".
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

Details on Gap and Overlap
----------==--------------

THIS SECTION IS UNDER DEVELOPMENT
---------------------------------

For a given dovetail spacing or template,

* <b>if you have an interference fit (too much overlap), then *decrease* the bit depth;</b>
* <b>if the fit is too loose (too much gap), then *increase* the bit depth.</b>

It's that simple, at least for half-blind dovetails, where increasing or
decreasing the depth a small amount is not an issue.  But that may not be
feasible if you're doing through dovetails and really want a particular stock
thickness.  Even for half-blinds, it's helpful to know good starting points
for the depth.  That's where the remainder of this
section may help.

The rest of this section gives details on how to determine the gap and
overlap for a given bit.  Some math is required, but it's not too bad, and you
can always skip the math go to right to the tables below.  And in the end, don't
trust my math.  Always use scrap wood to test the fit.

The minimum dovetail spacing used by {{ site.codename }} is given by

* `spacing = 2 I ROUND ((bit_width -  T bit_depth) / I)`.

where

* `I` is the increment size for the Incra:  `I = 1/32"` for English, `I = 1
  mm` for metric.
* `T = tan(bit_angle)`, where `tan` is the trigonometric tangent function.
* `ROUND(x)` rounds any decimal value `x` to the nearest integer. For
  example, `ROUND(1.4) = 1` and `ROUND(1.6) = 2`.

The formula above will also reproduce the dovetail examples given in the Incra Master Guide.
The `ROUND` function is what keeps the dovetail spacing in increments of `I`,
so that you can position any given router pass quickly and easily with the Incra LS Positioner.
But it's also what results in gap or overlap.

The gap and overlap are given by the relation

* `G = bit_depth T - I ROUND(T bit_depth / I)`

where`G` is negative for a gap and positive for an overlap.  A small amount of
gap or overlap may be acceptable.  But the maximum gap or overlap is `I/2`, or
`1/64"` for English units.  I believe that's too much, particularly for
overlap, and the rest of this section discusses how that can be avoided.

For an exact fit, we want `G = 0`.  The `bit_depth` values that give an
exact fit are integer multiples of `BD0`, where

* `BD0 = I / T`

The table below gives `BD0` for typical bits and `I=1/32"`.

| Bit Angle (deg) | BD0 (in)      | Nearest 1/32" |
|:---------------:|:-------------:|:-------------:|
|     7           | 0.2545        |  1/4          |
|     7.5         | 0.2374        |  7/32         |
|     9           | 0.1973        |  3/16         |
|     10          | 0.1772        |  5/32         |
|     14          | 0.1253        |  1/8          |

As an example, for the 9 degree bit, the fit will be exact for depths of
`0.197"`, twice that depth (`0.395"`), three times (`0.592"`), and so on.
The corresponding `Nearest 1/32"` are `3/16"`, `3/8"`, and `9/16"`, and so
on. By "Nearest", I mean by decreasing the depth, so that a small amount of
gap is created.

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/template/">Prev: Template Details</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/saving_preferences/">Next: Saving Preferences</a>
  </p>
</div>
<div style="clear: both;"></div>
