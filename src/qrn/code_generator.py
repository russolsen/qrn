import re
import sys
from io import StringIO
from contextlib import redirect_stdout
import qrn.utils as utils
import logging

SplitRE = r'(?=<%)|=%>\n?|!%>\n?|%>'

START_RE = re.compile(r'.*:$')
END_RE = re.compile(r' *end *$')

class CodeGenerator:
    def __init__(self, desc="Template"):
        self.desc = desc
        self.clear()
        self.depth = 0

    def clear(self):
        self.output = ''

    def _write(self, *values):
        for v in values:
          self.output += str(v)

    def indent(self):
        self.depth += 1

    def dedent(self):
        self.depth -= 1

    def emit_indent(self):
        self._write(' '*(self.depth*2))

    def text(self, text):
        self.emit_indent()
        self._write('print(', repr(text), ', end="")\n')

    def expr(self, expr):
        self.emit_indent()
        self._write('print(', expr, ', end="")\n')

    def code(self, code):
        self.emit_indent()
        self._write(f'{code}\n')

    def compile(self):
        self.compiled = utils.compile_string(self.output, self.desc)

    def render(self, glob, loc={}):
        self.clear()
        self.emit_body()
        result = utils.exec_prog_output(self.compiled, glob, loc)
        return result
