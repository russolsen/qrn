import logging
from functools import partial
import qrn.utils as utils
from qrn.kv import KV

# Pull in all of the code from qrn.assets and some selected
# functions from utils so that the user writing site.py 
# does not have to fish around in multiple namespaces.

from qrn.assets import *
from qrn.utils import mk_dirs, pp, emap, with_keys

def make_site(title, url, root, out_root):
    site = KV(title=title, url=url, 
            root=root, out_root=out_root, cate_index={})
    return site

def init_logging(path='log_site.txt', level=logging.INFO, filemode='w'):
    fmt='%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(filename=path, level=level, format=fmt, filemode=filemode)

def scan(directory, pats, exclusions=[], include_dirs=False):
    """Python version of the find command."""

    logging.info('Scan files dir: %s pats %s', directory, pats)
    paths = set()
    for g in pats:
        these_paths = utils.xglob(directory, g)
        paths = paths.union(set(these_paths))

    result = []
    for p in paths:
        if utils.globs(exclusions, p):
            continue
        result.append(p)
    
    if not include_dirs:
        result = filter(partial(utils.is_file, directory), result)
    return list(result)

