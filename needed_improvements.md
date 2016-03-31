---
layout: page_doc
title: Needed Improvements
---

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

<div id="textbox">
  <p class="alignleft">
    <a href="{{ site.baseurl }}/saving_preferences/">Prev: Saving Preferences</a>
  </p>
  <p class="alignright">
    <a href="{{ site.baseurl }}/additional_resources/">Next: Additional Resources</a>
  </p>
</div>
<div style="clear: both;"></div>
