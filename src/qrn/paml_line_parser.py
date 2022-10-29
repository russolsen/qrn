import re
import logging
import qrn.paml_node as paml_node

class PamlLineParser:
    def __init__(self, text):
        #print(f'txt: {text}')
        self.text = text
        self.ichar = 0

    def getc(self):
        if self.ichar >= len(self.text):
            return None
        result = self.text[self.ichar]
        self.ichar += 1
        return result

    def backup(self):
        if self.ichar <= 0:
            print("Error: backing up too far.")
        self.ichar -= 1

    def peek(self):
        result = self.getc()
        self.backup()
        return result

    def remaining(self):
        return self.text[self.ichar:]

    def get_word(self):
        result = ''
        ch = self.getc()
        while ch and re.match(r'[\w\-]', ch):
            result += ch
            ch = self.getc()
            #print(f'ch: {ch}')
        self.backup()
        #print(f'get word returning {result}')
        return result

    def get_attrs(self):
        result = '{'
        ch = self.getc()
        #print(f'ch: {ch}')
        while ch and ch != '}':
            result += ch
            ch = self.getc()
            #print(f'ch: {ch}')
        if ch != '}':
            print(f"Error: unclosed brace in {result}")
        result += ch
        return result

    def parse(self):
        ch = self.peek()
        if ch == '-':
            return self.parse_command()
        if ch == '=':
            return self.parse_expression()
        elif ch in ['%', '.', '#']:
            return self.parse_element()
        else:
            return self.parse_content()

    def parse_content(self):
        text = self.remaining().strip()
        return paml_node.ContentNode(text)

    def parse_command(self):
        self.getc()
        text = self.remaining().strip()
        return paml_node.CommandNode(text)

    def parse_expression(self):
        self.getc()
        text = self.remaining().strip()
        return paml_node.ExpressionNode(text)

    def parse_element(self):
        eltype = 'div'
        classes = []
        elid = ''
        attrs = {}
        eval_text = False
        text = ''

        ch = self.getc()
        while ch != None:
            if ch == '-':
                eltype = 'command'
                break
            if ch == '%':
                eltype = self.get_word()
            elif ch == '.':
                clz = self.get_word()
                classes.append(clz)
            elif ch == '#':
                elid = self.get_word()
            elif ch == '{':
                attrs = eval(self.get_attrs())
                if not isinstance(attrs, dict):
                    raise(Exception(f'Does not eval to a dictionary: {attrs}'))
            elif ch == '=':
                eval_text = True
                break
            elif ch == ' ':
                break
            ch = self.getc()

        text = self.remaining().strip()

        return paml_node.ElementNode(eltype, classes, elid, attrs, eval_text, text)
