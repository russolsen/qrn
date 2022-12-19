import re
import sys
from io import StringIO
import logging
from contextlib import redirect_stdout
import qrn.utils as utils
from qrn.code_generator import CodeGenerator

SplitRE = r'(?=<%)|=%>\n?|!%>\n?|%>'

CODE_RE = re.compile(r'^<%')
ESCAPE_RE = re.compile(r'^<%%')
END_ESCAPE = re.compile(r'^%%>')
END_RE = re.compile(r'^<%! *end *$')
ELSE_RE = re.compile(r'^<%! *else: *$')
ELIF_RE = re.compile(r'^<%! *elif .*:')
EX_RE = re.compile(r'^<%!')
INC_RE = re.compile(r'^<%=')

def _compile_template(fragments):
    generator = CodeGenerator()
    for frag in fragments:
        if not CODE_RE.search(frag):
            generator.text(frag)
        elif ESCAPE_RE.search(frag):
            logging.debug('escape: %s', frag)
            generator.text('<%')
            generator.text(frag[3:])
        elif END_ESCAPE.search(frag):
            logging.debug('end escape: %s', frag)
            generator.text('%>')
        elif END_RE.search(frag):
            generator.dedent()
        elif ELSE_RE.search(frag) or ELIF_RE.search(frag):
            generator.dedent()
            code = frag[3:].strip()
            generator.code(code)
            generator.indent()
        elif EX_RE.search(frag):
            code = frag[3:].strip()
            generator.code(code)
            if code[-1] == ':':
                generator.indent()
        elif INC_RE.search(frag):
            expr = frag[3:]
            generator.expr(expr)
    if generator.depth != 0:
        print("Generator depth:", generator.depth)
        #raise Exception("Unclosed blocks in epy template!")
    return generator.output

def source_code_for(ttext):
    fragments = re.split(SplitRE, ttext)
    output = _compile_template(fragments)
    return output

def template_from_text(ttext, desc='template'):
    output = source_code_for(ttext)
    code = utils.compile_string(output, desc)
    return code
