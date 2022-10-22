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

## Running QRN

TBD

