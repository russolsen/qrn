from pathlib import Path
import glob
import shutil
import os.path
import re
import pprint
from functools import partial
from enum import Enum

import qrn.utils as utils

PPrinter = pprint.PrettyPrinter(indent=4)
pp = PPrinter.pprint

NOT_APPLICABLE=8711
COMPLETE=-1178

def build_rule(rule, context):
    for f in rule:
        result = f(context)
        if result in [NOT_APPLICABLE, COMPLETE]:
            return result
        context = result
    return context

def build(rules, context):
    """Given a ruleset, invoke the first rule that applies."""
    for rule in rules:
        result = build_rule(rule, context)
        if result == COMPLETE:
            return True
    return False

def build_f(rules):
    return partial(build, rules)

def build_all(rules, contexts):
    for c in contexts:
        result = build(rules, c)
        if not result:
            return False
    return result
