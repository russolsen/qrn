import sys
import re
import glob
import fnmatch
import os
import os.path
import yaml
import pprint
import subprocess
import logging
from functools import partial
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

PPrinter = pprint.PrettyPrinter(indent=4)
pp = PPrinter.pprint

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

def write_yaml(data, path):
    with open(path, 'w') as f:
        yaml.dump(data, f)

def read_header(path):
    logging.debug('Read header: %s', path)
    text = __read_header_text(path)
    if text:
        return yaml.safe_load(text)
    return {}

def read_body(path):
    with open(path) as f:
        if __has_header(f):
            __read_until_match(f, MarkerRE)
            __read_until_match(f, MarkerRE)
        result = f.read()
        return result

def xglob(directory, pat):
    cwd = os.getcwd()
    os.chdir(directory)
    result = glob.glob(pat, recursive=True)
    os.chdir(cwd)
    return result

def find_paths(pat, skip=True):
    matches = glob.glob(pat, recursive=True)
    if skip:
        matches = filter(
                lambda path: not re.search('/_', path),
                matches)
    return emap(Path, matches)

def match_pat(pat, include_all=False):
        spaths = glob.glob(pat)
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
    new_dirs = Path(new_dir).parts
    parts = list(path.parts)
    parts[0:len(new_dirs)] = new_dirs
    result = Path(*parts)
    if suffix:
        result = result.with_suffix(suffix)
    return result

def globs(globs, fn):
    for g in globs:
        if fnmatch.fnmatch(fn, g):
            return True
    return False


def mk_dirs(directory, *paths):
    os.makedirs(directory, exist_ok=True)
    for path in paths:
        d = f'{directory}/{path}'
        logging.info('Making dir %s', d)
        os.makedirs(d, exist_ok=True)

def newer(path1, path2):
    try:
        p1_mod = os.path.getmtime(path1)
    except FileNotFoundError:
        return False

    try:
        p2_mod = os.path.getmtime(path2)
    except FileNotFoundError:
        return True

    return p1_mod > p2_mod

def is_file(directory, path):
    path = f'{directory}/{path}'
    return os.path.isfile(path)

def directories(paths):
    dirs = filter(identity, map(os.path.dirname, paths))
    return sorted(set(dirs))


def always(v):
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

def compile_string(s, desc):
    logging.debug('compile string [[%s]]', s)
    logging.debug('compile desc [[%s]]', desc)
    result = compile(s, desc, "exec")
    logging.debug('compile string result %s', result)
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

