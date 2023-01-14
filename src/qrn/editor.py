"""Edit QRN content files."""

from pathlib import Path
import logging
import qrn.utils as utils


def update_header(pat, **kvs):
    paths = utils.match_pat(pat)
    for path in paths:
        h, b = utils.read_structured(path)
        for k in kvs:
            v = kvs[k]
            if v == None:
                if k in h:
                    h.pop(k)
            else:
                h[k] = v
        utils.write_structured(h, b, path)

