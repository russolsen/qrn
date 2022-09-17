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
        #self.output += 'from io import StringIO\n'
        #self.output += '_f = StringIO()\n'

    def _write(self, value):
        #print("compiler, write:", value)
        logging.debug("CodeGenerator: write %s", value)
        self.output += str(value)

    def indent(self):
        self.depth += 1
        logging.debug("CodeGenerator: indent %s", self.depth)

    def dedent(self):
        self.depth -= 1
        logging.debug("CodeGenerator: dedent %s", self.depth)

    def emit_indent(self):
        self._write(' '*(self.depth*2))

    def text(self, text):
        self.emit_indent()
        self._write('print(')
        self._write(repr(text))
        self._write(', end="")\n')

    def expr(self, expr):
        self.emit_indent()
        self._write('print(')
        self._write(expr)
        self._write(', end="")\n')

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
