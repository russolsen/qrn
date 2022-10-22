import subprocess
import logging

# This file is the interface to the major non-python
# dependencies used by doctrine. They are program
# that converts sass to css and one that turns markdown
# into html. Currently we use the sass program and pandoc.

def md_to_html(content):
    """Convert markdown to html."""
    output = _pandoc(content, 'markdown', 'html')
    return output

def sass_to_css(ipath, opath):
    """Convert a scss/sass file to a css file."""
    logging.info('Sass conversion: %s => %s', ipath, opath)
    cmd_list = ['sass', ipath, opath]
    _run_external(cmd_list)
    return

def _run_external_filter(cmd_list, itext):
    """Given an argv array and some input, run a command, return output."""
    result = subprocess.run(
            cmd_list, 
            capture_output=True, 
            text=True, input=itext)

    result.check_returncode()
    return result.stdout

def _run_external(cmd_list):
    """Given an argv array, run a command, return output."""
    result = subprocess.run( cmd_list, capture_output=False )
    result.check_returncode()
    return result.stdout

def _pandoc(content, ipd, opd):
    """Run pandoc, converting from to/from the given formats."""
    cmd_list = ['pandoc', '--from', ipd, '--to', opd]
    output = _run_external_filter(cmd_list, content)
    return output
