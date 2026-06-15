IVOA document preparation from Markdown
=======================================

This is intended to allow the source document to be written in Markdown rather than LaTeX, and then processed into the various output formats (HTML, PDF ) using `pandoc <https://pandoc.org>`_.
It tries to share as much of the ivoaTeX infrastructure as possible, to avoid duplication of effort and to allow the choice for a document to be authored in either way. There are pros and cons to both approaches, and the choice is left to the author. The Markdown approach is intended to be simpler and more accessible, but it may not be able to produce all of the features that LaTeX can.

One of the issues with Markdown is that is is not a standard, and there are many different implementations of it. This implementation uses `pandoc markdown <https://pandoc.org/MANUAL.html#pandocs-markdown>`_, which does offer a number of extensions to the basic Markdown syntax, but that also means that the markdown is more able to offer features found within ivoaTeX, but it also means that the markdown is more complex and less portable than 'minimal' Markdown.


Installation Requirements
-------------------------

The following software is required to be installed on your system:

* `pandoc <https://pandoc.org>`_ (version 3.1 or later)
* `weasyprint <https://weasyprint.org/>`_ (for HTML to PDF conversion)


Implementation Notes
--------------------

The "usual" way that pandoc creates a PDF is to use LaTeX as an intermediate step, but this has the disadvantage that it requires a full LaTeX installation, which can be quite large and complex. This implementation uses `weasyprint <https://weasyprint.org/>`_ to convert HTML to PDF, which is simpler and more lightweight.

There is still the option to use LaTeX as an intermediate step, and there is a latex template provided for that purpose.
