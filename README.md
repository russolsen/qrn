# QRN: A simple, highly opinionated static site generator

QRN is a static site generator that is as simple as I can make
it while still being useful. QRN assumes that most of your content
is in markdown format, that you are using sass/scss or plain old css
for styling. QRN is also geared towards modest sized content, the
kind of thing you might find in a personal blog.

QRN also supports a simple but flexible layout/templating system
that let's you specify a standard HTML "frame" around your content
and also embed executable Python code in the content.

A key feature of QRN is that it has very few external dependencies.
QRN is written in a fairly generic Python 3 and requires:

* The PyYAML Python library.
* An external program that turns markdown into HTML (currently pandoc).
* And external program that turns scss/sass into css (currently sass).

That's it. What this means is that QRN is easy to set up and
(I hope) will continue to work over time as libararies and packages
change.

## What does QRN mean?

Ham radio operators use a [shorthand code](https://fieldradio.org/ham-radio-q-codes)
that has its origins in the early days of telegraphy. QRN is the code that means
"I am troubled by static noise."

## Using QRN

QRN works like most static site generators: You prepare a directory with
roughly the content you want to show up in your final site. When you run
QRN it transforms your source content into a final output site that you can
then deploy. The value of QRN is that it performs various transformation as
it does the copying:

* QRN knows how to tranform markdown files into html.
* QRN knows how to do "include" processing on your content so 
common headers and footers
The key idea behind QRN is that it is extremely opinionated about a few
things -- mostly around a some key file naming conventions and how those
files are processed into your final static webstite.

Specifically: 

* QRN wants you to put the source for your site under a directory called `src`.
* QRN generally ignores files and directories whose names start with an underbar (.e.g. `src/_save`).
* QRN wants you to put the source for all included files and layouts (see below) in `src/_layouts`.
* When you run QRN it will put the resulting processed, read-to-go site in a directory called `build`.
* QRN will run all files with a `.html` or `.xml` extension through the `epy` processor (see below).
* QRN will run all files with a `.haml` extension through the `paml` processor (see below).
* QRN will run all files with a `.md` extension through the `epy` processor and then convert it to HTML. 
* QRN will run all files with a `.sass` or `.scss` extension throug the `sass` processor.
* Otherwise, QRN will just copy files from `src` to `build`.

## File headers and layouts.

In general, QRN will recognize YAML headers at the beginning of .md, .html, .xml and .haml files. The headers
are set off from the file content with three dashes:

```
---
title: A simple html file.
date: klsdfklj
---
<html>
  <body>
    <title>A simple html file.</title>
  </body>
</html>
```

## The EPy Processor

As mentioned above, QRN runs .md, .html and .xml files through the Embedded Python (or EPy) processor.
EPy allows you to embed code that is evaluated at site build time in your content. 
EPy uses the common `text <%= some_code() %> more text` syntax, reminencent of
[Embedded Ruby](https://en.wikipedia.org/wiki/ERuby). Specifically:

* `<%= some_code() %>` will insert the result of evaluating the Python code into the text. Thus `1 <%= 100/50 %> 3`
will result in `1 2 3`.
* `<%! other_code() !%>` will simply evaluate the Python code and ignore the result.

Python's indentation based approach to syntax presents a special challenge to EPy: Requiring significant whitespace
in embedded code would be error prone and confusing. Instead, EPy strips off leading whitespace and relies on the
training `:`'s to open code blocks and a special <%! end %> directive to  close them. Here, for example is a
loop in EPy:

```
<%! for x in range(1): %>
The number is <%= x %>
<%! end %>
```

And an `if` statement in EPy:

```
<%! count = 0 %>
<%! if count: %>
The count is non-zero.
<%! else: %>
The counts is zero.
<%! end %>
```

Note that the `<%! end %>` does not appear in the actual Python code. It
is just a marker that the `if` or `for` has ended.

## The Paml Processor
