from pathlib import Path
import glob
import shutil
import os.path
import re
from functools import partial
from enum import Enum
import qrn.utils as utils

NOT_APPLICABLE=utils.Special('NA')
COMPLETE=utils.Special('CO')

def build_rule(rule, context):
    for f in rule:
        result = f(context)
        if result in [NOT_APPLICABLE, COMPLETE]:
            return result
        context = result
    return context

def build_rule_f(rule):
    def _build_rule(context):
        return build_rule(rule, context)
    return _build_rule

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
