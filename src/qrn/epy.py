import re
import sys
from io import StringIO
import logging
from contextlib import redirect_stdout
import qrn.utils as utils
from qrn.code_generator import CodeGenerator

SplitRE = r'(?=<%)|=%>\n?|!%>\n?|%>'

CODE_RE = re.compile(r'^<%')
END_RE = re.compile(r'^<%! *end *$')
EX_RE = re.compile(r'^<%!')
INC_RE = re.compile(r'^<%=')

def _compile_template(fragments):
    generator = CodeGenerator()
    for frag in fragments:
        if not CODE_RE.search(frag):
            generator.text(frag)
        elif END_RE.search(frag):
            generator.dedent()
        elif EX_RE.search(frag):
            code = frag[3:].strip()
            generator.code(code)
            if code[-1] == ':':
                generator.indent()
        elif INC_RE.search(frag):
            expr = frag[3:]
            generator.expr(expr)
    return generator.output

def make_template(ttext, desc='template'):
    fragments = re.split(SplitRE, ttext)
    output = _compile_template(fragments)
    code = utils.compile_string(output, desc)
    return code

def make_template_f(ttext, desc='template'):
    code = make_template(ttext, desc)
    def render(globs={}, locs={}):
        return utils.exec_prog_output(code, globs, locs)  
    return render
