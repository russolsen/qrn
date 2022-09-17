import logging
import qrn.utils as utils

# Pull in all of the code from qrn.assets and some selected
# functions from utils so that the user writing site.py 
# does not have to fish around in multiple namespaces.

from qrn.assets import *
from qrn.utils import mk_dirs, pp, emap, with_keys, scan, partition

def init_logging(path=None, level=logging.INFO, filemode='w'):
    fmt='%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(filename=path, level=level, format=fmt, filemode=filemode)
