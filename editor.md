---
layout: page_doc
title: Editor
---

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

<figure class="zoomable">
<a name="figure8">
<img src="{{ site.baseurl }}/images/editor_screen_shot.png">
</a>
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
