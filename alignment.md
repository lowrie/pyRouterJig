---
layout: page_doc
title: Alignment of Router Passes
---

This section discusses how router passes are positioned in general.  For
template alignment, see the
<a href="{{ site.baseurl }}/template/">section Template Details</a>.

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
<b>Preferences</b>; see the 
<a href="{{ site.baseurl }}/saving_preferences/">section Saving Preferences</a>.

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/double_joints/">Prev: Double Joints</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/menus/">Next: Drop-down Menus</a>
  </p>
</div>
<div style="clear: both;"></div>
