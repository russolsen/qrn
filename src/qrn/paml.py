'''Like HAML, but with Python.'''

import re
import logging
import qrn.utils as utils
from qrn.code_generator import CodeGenerator
from qrn.paml_line_parser import PamlLineParser

INDENT = utils.Special('==>')
OUTDENT = utils.Special('<==')
EOF = utils.Special('eof')

SPACING = 2

def indent_level(s):
    for n in range(len(s)):
        if (s[n] != ' '):
            return [n / SPACING, s[n:]]

class PamlParser:
    '''Parse the HAML-like Paml text.'''
    def __init__(self, lines):
        self.tokens = []
        self.tokenize_lines(lines)
        self.itoken = 0

    def tokenize_lines(self, lines):
        depth = 0
        for line in lines:
            line = line.rstrip()
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
            logging.debug('New line: [%s]', line)
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
        logging.debug("Paml read token %s", result)
        self.itoken += 1
        return result

    def peek_tokens(self, n=5):
        if self.itoken >= len(self.tokens):
            return []
        return self.tokens[self.itoken:self.itoken+n]

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
        logging.debug("reading collection %s", tok)
        while tok != OUTDENT and (tok != EOF):
            self.unread_token()
            logging.debug("reading collection %s", tok)
            expr = self.read_node()
            result.append(expr)
            tok = self.read_token()
        return result

    def read_node(self):
        header = self.read_token()
        if header == EOF:
            logging.debug('eof')
            return None
        elif (header == INDENT):
            logging.warning('unex indent, next tokens:')
            logging.warning(self.peek_tokens())
            raise Exception('Unexpected indent')
        elif (header == OUTDENT):
            logging.warning('unex outdent, next tokens')
            logging.warning(self.peek_tokens())
            raise Exception('Unexpected outdent')
        
        children = []
        tok = self.peek_token()
        if tok == INDENT:
            self.read_token()
            children = self.read_collection()

        node = PamlLineParser(header).parse()
        if children:
            node.add_all(children)
        return node

def template_from_text(text, desc='template'):
    '''Return the Python compiled code for the Paml text.'''
    lines = text.split('\n')
    parser = PamlParser(lines)
    generator = CodeGenerator()
    node = parser.read_node()
    while node:
        node.expand(generator)
        node = parser.read_node()
    logging.debug("template from text, len of gen output %s", len(generator.output))
    code = utils.compile_string(generator.output, desc)
    logging.debug("code: %s", code)
    return code
