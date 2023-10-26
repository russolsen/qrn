'''Programatic interface to create Python code.'''

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
    '''Create Python code.'''

    def __init__(self, desc="Template"):
        self.desc = desc
        self.clear()
        self.depth = 0

    def clear(self):
        '''Start over: clear all of the accumulated output.'''
        self.output = ''

    def _write(self, *values):
        for v in values:
          self.output += str(v)

    def indent(self):
        '''Indent the Python code by one level.'''
        self.depth += 1

    def dedent(self):
        '''Decrease the the Python code indentation by one level.'''
        self.depth -= 1

    def emit_indent(self):
        '''Write the current indentation to the output.'''
        self._write(' '*(self.depth*2))

    def text(self, text, line_no=None):
        '''Write a print statement to print the text to the output.'''
        if line_no:
            self.emit_indent()
            self._write(f'line_no={line_no}')
        self.emit_indent()
        self._write('print(', repr(text), ', end="")\n')

    def expr(self, expr, line_no=None):
        '''Write a print statement to print the results of the expression to the output.'''
        if line_no:
            self.emit_indent()
            self._write(f'line_no={line_no}')
        self.emit_indent()
        self._write('print(', expr, ', end="")\n')

    def code(self, code):
        '''Write a some code to the output.'''
        self.emit_indent()
        self._write(f'{code}\n')

    def compile(self):
        '''Compile the generated code and return the result.'''
        self.compiled = utils.compile_string(self.output, self.desc)
