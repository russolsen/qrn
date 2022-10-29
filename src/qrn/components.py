from pathlib import Path
import shutil
import logging
import qrn.utils as utils
from qrn.pipeline import NOT_APPLICABLE, COMPLETE

def to_dependency_f(target_dir, suffix=None, other_deps=[]):
    def to_dependancy(path):
        opath = utils.relocate(path, target_dir, suffix)
        logging.debug('To dep %s => %s', path, opath)
        return {'output': opath, 'sources':([path] + other_deps)}
    return to_dependancy

def is_suffix_f(*suffixes):
    def _is_suffix(path):
        if path.suffix in suffixes:
            return path
        return NOT_APPLICABLE
    return _is_suffix

def is_dir(path):
    if path.is_dir():
        return path
    return NOT_APPLICABLE

def isoutdated(context):
    output = context['output']
    sources = context['sources']
    for s in sources:
        if utils.newer(s, output):
            logging.info('Ouput file %s is out of date wrt %s.', output, s)
            return context
    logging.info('Up to date: %s', output)
    return COMPLETE

def ispublished(context):
    attrs = context['attrs']
    published = attrs.get('published', True)
    if published:
        return context
    return COMPLETE
    
def copy_file(context):
    """Copy a file, unchanged."""
    ipath = context['sources'][0]
    opath = context['output']
    logging.info("Copy file %s => %s", ipath, opath)
    shutil.copyfile(ipath, opath)
    return context

def print_it(context):
    print("Print it: ", end='')
    utils.pp(context)
    return context

def print_keys(context):
    print("Print it: ", end='')
    utils.pp(context)
    return context

def print_path_f(msg):
    def _print_path(context):
        print(msg, context['output'])
        return context
    return _print_path

def read_attrs(context):
    opath = context['output']
    ipath = context['sources'][0]
    attrs = utils.read_header(ipath)
    attrs['ipath'] = ipath
    attrs['opath'] = opath
    context['attrs'] = attrs
    return context

def create_dir(context):
    opath = context['output']
    if not opath.is_dir():
        print("Creating directory", opath)
        logging.info('Create dir %s', opath)
        opath.mkdir(parents=True, exist_ok=True)
    return context
