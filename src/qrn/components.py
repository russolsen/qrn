'''Functions to help build the processing pipeline.'''

from pathlib import Path
import shutil
import logging
import qrn.utils as utils
from qrn.pipeline import NOT_APPLICABLE, COMPLETE

def to_dependency_f(target_dir, suffix=None, other_deps=[]):
    '''Return a function that will generate dependancies to a given dir and suffix.'''
    def to_dependancy(path):
        opath = utils.relocate(path, target_dir, suffix)
        logging.debug('To dep %s => %s', path, opath)
        return {'output': opath, 'sources':([path] + other_deps)}
    return to_dependancy

def is_suffix_f(*suffixes):
    '''Return a function that tests if a path has one of the suffixes.'''
    def _is_suffix(path):
        if path.suffix in suffixes:
            return path
        return NOT_APPLICABLE
    return _is_suffix

def is_dir(path):
    '''Pipline function that tests if the given path is a directory.'''
    if path.is_dir():
        return path
    return NOT_APPLICABLE

def isoutdated(context):
    '''Pipline function that checks if any one of the sources is out of date.'''
    output = context['output']
    sources = context['sources']
    for s in sources:
        if utils.newer(s, output):
            logging.info('Ouput file %s is out of date wrt %s.', output, s)
            return context
    logging.info('Up to date: %s', output)
    return COMPLETE

def ispublished(context):
    '''Pipline function that checks the published attribute.'''
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
    '''Debugging pipline function.'''
    print("Print it: ", end='')
    utils.pp(context)
    return context

def print_keys(context):
    '''Debugging pipline function.'''
    print("Print it: ", end='')
    utils.pp(context)
    return context

def print_path_f(msg):
    '''Return a pipeline function that prints the output path with a message.'''
    def _print_path(context):
        print(msg, context['output'])
        return context
    return _print_path

def read_attrs(context):
    '''Read the attributes from the input file and roll into the context.'''
    opath = context['output']
    ipath = context['sources'][0]
    attrs = utils.read_header(ipath)
    attrs['ipath'] = ipath
    attrs['opath'] = opath
    context['attrs'] = attrs
    return context

def create_dir(context):
    '''Pipeline function to create the output directory.'''
    opath = context['output']
    if not opath.is_dir():
        print("Creating directory", opath)
        logging.info('Create dir %s', opath)
        opath.mkdir(parents=True, exist_ok=True)
    return context
