import re
import logging
import qrn.utils as utils
import qrn.paml_node as paml_node
from qrn.code_generator import CodeGenerator
from qrn.paml_line_parser import PamlLineParser

class Special:
    """Special tokens."""

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return f'Special({self.tag})'

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.tag == other.tag

    def __hash__(self):
        return hash(self.tag)

INDENT = Special('==>')
OUTDENT = Special('<==')
EOF = Special('eof')

SPACING = 2

def indent_level(s):
    #print(f"indent level {s} {type(s)} {len(s)}")
    for n in range(len(s)):
        if (s[n] != ' '):
            return [n / SPACING, s[n:]]

class PamlParser:
    def __init__(self, lines):
        self.tokens = []
        self.tokenize_lines(lines)
        self.itoken = 0

    def tokenize_lines(self, lines):
        depth = 0
        for line in lines:
            line = line.rstrip()
            #print('New line: [%s]', type(line), line)
            if not line:
                continue
            this_depth, line = indent_level(line)
            while this_depth > depth:
                self.tokens.append(INDENT)
                depth += 1
            while this_depth < depth:
                self.tokens.append(OUTDENT)
                depth -= 1
            self.tokens.append(line)

    def read_line(self):
        if 0 == len(self.tokens):
            if self.iline >= len(self.lines):
                self.tokens = [EOF]
                return
            line = self.lines[self.iline]
            self.iline += 1
            line = line.rstrip()
            logging.info('New line: [%s]', line)
            this_depth, line = indent_level(line)
            while this_depth > self.depth:
                self.tokens.append(INDENT)
                self.depth += 1
            while this_depth < self.depth:
                self.tokens.append(OUTDENT)
                self.depth -= 1
            self.tokens.append(line)
            #print(f'at the end of readline, tokens: {self.tokens}')

    def read_token(self):
        if self.itoken >= len(self.tokens):
            return EOF
        result = self.tokens[self.itoken]
        self.itoken += 1
        return result

    def peek_token(self):
        if self.itoken >= len(self.tokens):
            return EOF
        tok = self.tokens[self.itoken]
        #print(f'Peek token returns {tok}, tokens {self.tokens}')
        return tok

    def unread_token(self):
        self.itoken -= 1

    def read_collection(self):
        result = []
        tok = self.read_token()
        while tok != OUTDENT and (tok != EOF):
            self.unread_token()
            expr = self.read_node()
            result.append(expr)
            tok = self.read_token()
        return result

    def read_node(self):
        header = self.read_token()
        #print(repr(header))
        if header == EOF:
            logging.info('eof')
            return None
        elif (header == INDENT):
            logging.warning('unex outdent')
            raise Exception('Unexpected indent')
        elif (header == OUTDENT):
            logging.warning('unex outdent')
            raise Exception('Unexpected outdent')
        
        children = []
        tok = self.peek_token()
        if tok == INDENT:
            self.read_token()
            children = self.read_collection()

        #print(f"***Creating node with {header} and {children}")
        node = PamlLineParser(header).parse()
        #print(node)
        if children:
            #print(f'Adding children to node {node}: {children}')
            node.add_all(children)
        return node


def make_template(text, desc):
    lines = text.split('\n')
    parser = PamlParser(lines)
    generator = CodeGenerator()
    node = parser.read_node()
    while node:
        node.expand(generator)
        node = parser.read_node()
    code = utils.compile_string(generator.output, desc)
    return code

def make_template_f(text, desc="template"):
    code = make_template(text, desc)
    def render(globs={}, locs={}):
        return utils.exec_prog_output(code, globs, locs)
    return render
    
