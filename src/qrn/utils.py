import sys
import re
import glob
import fnmatch
import os
import os.path
import yaml
import pprint
import subprocess
from io import StringIO
from contextlib import redirect_stdout

from qrn.log import log

PPrinter = pprint.PrettyPrinter(indent=4)
pp = PPrinter.pprint

MarkerRE = r'^--- *$'

def read_file(path):
    log(f"Read file: {path}")
    result = None
    with open(path) as f:
        result = f.read()
    return result

def __read_until_match(f, regex):
    line = f.readline()
    while line:
        if re.search(regex, line):
            return line
        line = f.readline()
    return None

def __read_header_text(path):
    result = ''
    with open(path) as f:
        __read_until_match(f, MarkerRE)
        line = f.readline()
        while line:
            if re.search(MarkerRE, line):
                return result
            result += line
            line = f.readline()

def read_yaml(path):
    text = read_file(path)
    return yaml.safe_load(text)

def read_header(path):
    text = __read_header_text(path)
    return yaml.safe_load(text)

def read_body(path):
    with open(path) as f:
      __read_until_match(f, MarkerRE)
      __read_until_match(f, MarkerRE)
      return f.read()

def change_suffix(p, newsuffix):
    parts = os.path.splitext(p)
    return f'{parts[0]}.{newsuffix}'

def get_suffix(p):
    parts = os.path.splitext(p)
    return parts[1][1:]

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

def mk_dirs(*dirs):
    for d in dirs:
        log("Making dir", d)
        os.makedirs(d, exist_ok=True)

def outdated(src_path, dst_path):
    try:
        src_mod = os.path.getmtime(src_path)
        dst_mod = os.path.getmtime(dst_path)
        #print(src_path, dst_path, src_mod, dst_mod)
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
            result = f(result)
        return result
    return invoke

def doall(f, coll):
    """Like map, but not lazy."""
    return list(map(f, coll))

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
    log("---- Code ----")
    lines = code_str.split('\n')
    for i in range(len(lines)):
        log(i+1, lines[i])

def compile_string(s, desc):
    return compile(s, desc, "exec")

def exec_prog_output(compiled, glob={}, loc={}):
    """Execute the code supplied, returning it's stdout contents."""
    f = StringIO()
    try:
        with redirect_stdout(f):
            exec(compiled, glob, loc)
    except Exception as e:
        log("Error running code", e)
        raise e
    f.seek(0)
    result = f.read()
    f.close()
    return result

def exec_string_output(s, glob={}, loc={}, desc="Dynamically generated"):
    """Execute the string supplied as code, returning it's stdout contents."""
    compiled = compile_string(s)
    return exec_prog_output(compiled, glob, loc, desc)

