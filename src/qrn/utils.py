import datetime
import email.utils
import fnmatch
import glob
import logging
import os
import os.path
import pprint
import re
import subprocess
import sys
import time
import yaml
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

PPrinter = pprint.PrettyPrinter(indent=4)
pp = PPrinter.pprint

class Special:
    """Special unique values."""

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return f'Special({self.tag})'

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.tag == other.tag

    def __hash__(self):
        return hash(self.tag)

MarkerRE = r'^--- *$'

def read_file(path, mode='r'):
    logging.debug(f'Read file: %s', path)
    result = None
    with open(path, mode) as f:
        result = f.read()
    return result

def write_file(contents, path, mode='w'):
    logging.debug('Write file: %s', path)
    result = None
    with open(path, mode) as f:
        f.write(contents)

def __read_until_match(f, regex):
    line = f.readline()
    while line:
        if re.search(regex, line):
            return line
        line = f.readline()
    return None

def __read_header_text(path):
    with open(path) as f:
        if not __has_header(f):
            return ''
        result = ''
        f.readline()
        line = f.readline()
        while line:
            if re.search(MarkerRE, line):
                return result
            result += line
            line = f.readline()
    return result

def __has_header(f):
    line = f.readline()
    f.seek(0)
    return re.search(MarkerRE, line)

def read_yaml(path):
    text = read_file(path)
    if text:
        return yaml.safe_load(text)
    return {}

def read_header(path):
    """Read the header of a file."""
    logging.debug('Read header: %s', path)
    text = __read_header_text(path)
    if text:
        return yaml.safe_load(text)
    return {}

def read_body(path):
    """Given a path, read the body (i.e. w/o the header) of the file.
    Will return the entire file if there is no header."""
    with open(path) as f:
        if __has_header(f):
            __read_until_match(f, MarkerRE)
            __read_until_match(f, MarkerRE)
        result = f.read()
        return result

def match_pat(pat, include_all=False):
    """Given a glob pat, return matching files. If include_all is False,
    skip files that start with _."""
    spaths = glob.glob(pat, recursive=True)
    if include_all:
        return [Path(p) for p in spaths]
    paths = [Path(p) for p in spaths if not re.search('/_', p)]
    return paths

def match_pats(*pats, include_all=False):
    results = []
    for p in pats:
        results += match_pat(p, include_all)
    return results

def relocate(path, new_dir, suffix=None):
    """Given a path and a directory, replace the leading dir of the path
    with the new_dir. If a suffix is given, also replace the suffix."""
    parts = list(path.parts)
    wo_dir = parts[1:]
    result = Path(new_dir, *wo_dir)
    if suffix:
        result = result.with_suffix(suffix)
    return result

def newer(path1, path2):
    """Return true if path1 is newer than path2."""
    try:
        p1_mod = os.path.getmtime(path1)
    except FileNotFoundError:
        #logging.info('%s does not exist, False', path1)
        return False

    try:
        p2_mod = os.path.getmtime(path2)
    except FileNotFoundError:
        #logging.info('%s does not exist, True', path2)
        return True

    #logging.info('newer %s %s: %s > %s (%s)', path1, path2, p1_mod, p2_mod, p1_mod > p2_mod)
    result = p1_mod > p2_mod
    return result

def always(v):
    """Return a function that always returns v."""
    def _always(*args):
        return v
    return _always

def memoize(f):
    """Return a function that takes the same args as f but caches results."""
    cache={}
    def standin(*args):
        if args in cache:
            logging.info('Cache hit for %s.', args)
            return cache[args]
        result = f(*args)
        cache[args] = result
        return result
    return standin

def log_code(code_str):
    """Given code in a string, log it out line by line."""
    logging.debug('---- Code ----')
    lines = code_str.split('\n')
    for i in range(len(lines)):
        logging.debug('%d: %s', i+1, lines[i])

def format_rfc822(dtime):
    return email.utils.formatdate(time.mktime(dtime.timetuple()))

def format_now():
    return format_rfc822(datetime.datetime.now())

def compile_string(s, desc):
    result = compile(s, desc, "exec")
    return result

def exec_prog_output(compiled, glob={}, loc={}):
    """Execute the code supplied, returning it's stdout contents."""
    f = StringIO()
    try:
        with redirect_stdout(f):
            exec(compiled, glob, loc)
    except Exception as e:
        logging.warning("Error running code %s", e)
        raise e
    f.seek(0)
    result = f.read()
    f.close()
    return result

def exec_string_output(s, glob={}, loc={}, desc="Dynamically generated"):
    """Execute the string supplied as code, returning it's stdout contents."""
    compiled = compile_string(s)
    return exec_prog_output(compiled, glob, loc, desc)
