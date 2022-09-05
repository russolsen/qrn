import re
import sys
from io import StringIO
from contextlib import redirect_stdout
import qrn.utils as utils
import logging

SplitRE = r'(?=<%)|=%>\n?|!%>\n?|%>'

CODE_RE = re.compile(r'^<%')
END_RE = re.compile(r'^<%! *end *$')
EX_RE = re.compile(r'^<%!')
INC_RE = re.compile(r'^<%=')

class Template:
    def __init__(self, ttext, desc="Template"):
        self.ttext = ttext
        self.desc = desc
        self.fragments = re.split(SplitRE, ttext)
        self.compile()

    @classmethod
    def from_file(cls, path, desc):
        content = utils.read_file(path)
        return cls(content, desc)

    def clear(self):
        self.output = 'logging.debug("Running generated code.")\n'

    def write(self, value):
        self.output += str(value)

    def emit_indent(self, level):
        self.write(' '*(level*2))

    def emit_text(self, text, dent):
        self.emit_indent(dent)
        self.write('print(')
        self.write(repr(text))
        self.write(', end="")\n')

    def emit_expr(self, expr, dent):
        self.emit_indent(dent)
        self.write('print(')
        self.write(expr)
        self.write(', end="")\n')

    def emit_code(self, code, dent):
        self.emit_indent(dent)
        self.write(f'{code}\n')

    def emit_body(self):
        depth = 0
        for frag in self.fragments:
            if not CODE_RE.search(frag):
                self.emit_text(frag, depth)
            elif END_RE.search(frag):
                depth -= 1
            elif EX_RE.search(frag):
                code = frag[3:].strip()
                self.emit_code(code, depth)
                if code[-1] == ':':
                    depth += 1
            elif INC_RE.search(frag):
                expr = frag[3:]
                self.emit_expr(expr, depth)

    def compile(self):
        self.clear()
        self.emit_body()
        utils.log_code(self.output)
        self.compiled = utils.compile_string(self.output, self.desc)

    def render(self, glob, loc={}):
        self.clear()
        self.emit_body()
        result = utils.exec_prog_output(self.compiled, glob, loc)
        return result
