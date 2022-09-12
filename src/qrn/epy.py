import re
import sys
from io import StringIO
import logging
from contextlib import redirect_stdout
import qrn.utils as utils
from qrn.code_generator import CodeGenerator

import random

SplitRE = r'(?=<%)|=%>\n?|!%>\n?|%>'

CODE_RE = re.compile(r'^<%')
END_RE = re.compile(r'^<%! *end *$')
EX_RE = re.compile(r'^<%!')
INC_RE = re.compile(r'^<%=')

class EPyCompiler:
    """Embedded Python: Like ERb, but for Python."""

    def __init__(self, ttext, desc="Template"):
        self.ttext = ttext
        self.desc = desc
        self.fragments = re.split(SplitRE, ttext)
        self.compiled = None
        self.compile()

    @classmethod
    def from_file(cls, path, desc):
        content = utils.read_file(path)
        return cls(content, desc)

    def _compile_template(self, comp):
        for frag in self.fragments:
            if not CODE_RE.search(frag):
                comp.text(frag)
            elif END_RE.search(frag):
                comp.dedent()
            elif EX_RE.search(frag):
                code = frag[3:].strip()
                comp.code(code)
                if code[-1] == ':':
                    comp.indent()
            elif INC_RE.search(frag):
                expr = frag[3:]
                comp.expr(expr)

    def compile(self):
        #print(f"EPY: compile  <<{self.ttext[1:50]}>>", self.desc)
        generator = CodeGenerator()
        self._compile_template(generator)
        #print(f"Compiler result: <<<<{generator.output}>>>>")
        fn = f'{random.randint(1,100)}.txt'
        f = open(fn, "w")
        f.write(generator.output)
        f.close()
        self.compiled = utils.compile_string(generator.output, self.desc)

    def render(self, glob, loc={}):
        result = utils.exec_prog_output(self.compiled, glob, loc)
        return result

    def render_with_context(self, context):
        result = utils.exec_prog_output(self.compiled, globals(), locals())
        return result

    @classmethod
    def evaluate(cls, content, name, globs, locs):
        c = cls(content, name)
        return utils.exec_prog_output(c.compiled, globs, locs)

if __name__ == '__main__':
    f = open('ex.erb')
    text = f.read()
    t = EPyCompiler(text)
    print(t.render(globals()))
