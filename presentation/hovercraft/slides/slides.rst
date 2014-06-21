:title: Slideshow Tutorial
:author: Lennart Regebro
:description: The Hovercraft! tutorial.
:keywords: presentation, restructuredtext, impress.js, tutorial
:css: style.css

This slide show is a sort of tutorial of how to use Hovercraft! to make
presentations. It will show the most important features of Hovercraft! with
explanations. 

Hopefully you ended up here by the link from the official documentation at
https://hovercraft.readthedocs.org/ . If not, you probably want to go there
and read through it first.

This totorial is meant to be read as source code, not in any HTML form, so if
you can see this text (it won't be visible in the final presentation) and you
aren't seeing the source code, you are doing it wrong. It's going to be
confusing and not very useful. Again, go to the official docs. There are
links to the source code in the Examples section.

You can render this presentation to HTML with the command::

    hovercraft positions.rst outdir
    
And then view the outdir/index.html file to see how it turned out.

**Now then, on to the tutorial part!**

The first thing to note is the special syntax for information about the
presentation that you see above. This is in reStrcuturedText called "fields"
and it's used all the time in Hovercraft! to change attributes and set data
on the presentation, on slides and on images. The order of the fields is not
important, but you can only have one of each field.

The fields above are meta-data about the presentation, except for the
:css:-field. This meta data is only useful if you plan to publish the
presentation by putting the HTML online. If you are only going to show this
presentation yourself in a meeting you can skip all of it.

The title set is the title that is going to be shown in the title bar of the
browser. reStructuredText also have a separete syntax for titles that is also
supported by Hovercraft::

    .. title:: Slideshow Tutorial

However that requires an empty line after it, and it looks better to use the
same syntax for all metadata.

The :css: field will add a custom CSS-file to this presentation. This is
something you almost always want to do, as you otherwise have no control over
how the presentation will look. You can also specify different media for
the CSS, for example "screen,projection"::

    :css-screen,projection: hovercraft.css
    
This way you can have different CSS for print and for display. You can only
specify one CSS-file per field, however. If you want to include more you
need to use the @import directive in CSS.

Once you have added metadata and CSS, it's time to start on the slides.

You separate slides with a line that consists of four or more dashes. The
first slide will start at the first such line, or at the first heading. Since
none of the text so far has been a heading, it means that the first slide has
not yet started. As a result, all this text will be ignored in the output.

So lets start the first slide by having a line with four dashes. Since the
first slide starts with a heading, that line is strictly speaking not needed,
but it's good to be explicit.

----

=====================  ============================ ===================================
.. image:: ucl_bw.svg  Local Search for Multicast   .. image:: epl-mention-vertical.svg
    :height: 300px     in Software Defined Networks      :height: 300px
=====================  ============================ ===================================
=======================================================================================

Promoters
---------

    | Pr. Olivier Bonaventure
    | Pr. Yves Deville

Authors
-------

    | Jadin Kevin
    | Debroux Léonard

----

DUMMY!
=================

Graph:
<div id="chart"></div>
<script type="text/javascript">fillDiv("chart", "sota_setup-0_index-0.json", 1680, 900)</script>

----

:data-x: r3000
:data-y: r-1500
:data-scale: 15
:data-rotate-z: 0
:data-rotate-x: 0
:data-rotate-y: 90
:data-z: 0

Second slide!
=================

- So beauty
- Much wiggly
- Wow
