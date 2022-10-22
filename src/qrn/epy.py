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
    if generator.depth != 0:
        raise Exception("Unclosed blocks in epy template!")
    return generator.output

def template_from_text(ttext, desc='template'):
    fragments = re.split(SplitRE, ttext)
    output = _compile_template(fragments)
    code = utils.compile_string(output, desc)
    return code

def template_f_from_text(ttext, desc='template'):
    code = template_from_text(ttext, desc)
    def render(globs={}, locs={}):
        return utils.exec_prog_output(code, globs, locs)  
    return render

def template_f_from_path(path):
    text = utils.read_file(path)
    return template_f_from_text(text, path)
