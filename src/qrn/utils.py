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

def change_suffix(p, newsuffix):
    parts = os.path.splitext(p)
    return f'{parts[0]}.{newsuffix}'

def get_suffix(p):
    parts = os.path.splitext(p)
    return parts[1][1:]

def get_filename(p):
    parts = os.path.split(p)
    return parts[1]

def remove_suffix(p):
    parts = os.path.splitext(p)
    return parts[0]

def split_path(path):
    d = os.path.dirname(path)
    filename = os.path.basename(path)
    parts = os.path.splitext(filename)
    name = parts[0]
    suffix = parts[1][1:]
    return [d, name, suffix]

def xglob(directory, pat):
    cwd = os.getcwd()
    os.chdir(directory)
    result = glob.glob(pat, recursive=True)
    os.chdir(cwd)
    return result

def globs(globs, fn):
    for g in globs:
        if fnmatch.fnmatch(fn, g):
            return True
    return False

def scan(directory, pats, exclusions=[], include_dirs=False):
    """Python version of the find command."""

    logging.info('Scan files dir: %s pats %s', directory, pats)
    paths = set()
    for g in pats:
        these_paths = xglob(directory, g)
        paths = paths.union(set(these_paths))

    result = []
    for p in paths:
        if globs(exclusions, p):
            continue
        result.append(p)
    
    if not include_dirs:
        result = filter(partial(is_file, directory), result)
    return list(result)

def mk_dirs(directory, *paths):
    os.makedirs(directory, exist_ok=True)
    for path in paths:
        d = f'{directory}/{path}'
        logging.info('Making dir %s', d)
        os.makedirs(d, exist_ok=True)

def outdated(src_path, dst_path):
    try:
        src_mod = os.path.getmtime(src_path)
        dst_mod = os.path.getmtime(dst_path)
        return src_mod > dst_mod
    except FileNotFoundError:
        return True

def is_file(directory, path):
    path = f'{directory}/{path}'
    return os.path.isfile(path)

def directories(paths):
    dirs = filter(identity, map(os.path.dirname, paths))
    return sorted(set(dirs))

def get_filestem(p):
    parts = os.path.splitext(os.path.basename(p))
    return parts[0]

def assoc(d, *kvs):
    result = d.copy()
    for i in range(0, len(kvs), 2):
        result[kvs[i]] = kvs[i+1]
    return result

def with_keys(d, *ks):
    result = {}
    for k in ks:
        if k in d:
            result[k] = d[k]
    return result

def identity(x):
    return x

def compose(*funcs):
    """Return a function that cascasdes all of the supplied functions."""
    funcs = list(funcs)
    if (len(funcs) == 1) and (type(funcs[0]) == list):
      return compose(*funcs[0])
    elif len(funcs) == 1:
      return funcs[0]

    def invoke(arg):
        result = arg
        for f in funcs:
            #print('invoke, calling', f)
            result = f(result)
        return result
    return invoke

class _Multi:
    def __init__(self, dispatch_f, default_f=None):
       self.dispatch_f = dispatch_f
       self.default_f = default_f
       self.methods = {}

    def _add_method(self, dispatch_v, f):
        self.methods[dispatch_v] = f

    def __call__(self, *args):
        dispatch_v = self.dispatch_f(*args)

        f = self.methods.get(dispatch_v, self.default_f)
        return f(*args)

def defmulti(dispatch_f, default_f=None):
    return _Multi(dispatch_f, default_f)

def defmethod(mm, dispatch_f, f):
    mm._add_method(dispatch_f, f)


def arrow(x, *funcs):
    for f in funcs:
        x = f(x)
    return x

def doall(f, coll):
    """Apply f to each element in coll, do not keep results."""
    for element in coll:
        #print("do all call fun")
        f(element)
        #print("do all DONE call fun")

def emap(f, coll):
    """Like map, but not lazy."""
    return list(map(f, coll))

def partition(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def lfilter(f, coll):
    """Like filter, but not lazy."""
    return list(filter(f, coll))

def complement(f):
    """Returns a function that returns the logical not of the supplied function."""
    def not_f(*args):
        return not f(*args)
    return not_f

def memoize(f):
    """Return a function that takes the same args as f but caches results."""
    cache={}
    def standin(*args):
        if args in cache:
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
    return compile(s, desc, "exec")

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

