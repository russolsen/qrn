import re
import logging

class PamlNode:
    def __init__(self):
        self.children = []

    def add_child(self, kid):
        self.children.append(kid)

    def add_all(self, kids):
        logging.info("Add all: %s", kids)
        for k in kids:
            self.add_child(k)

    def _expand_children(self, generator):
        result = ''
        for kid in self.children:
            #print(f"encode kid: {type(kid)} {kid}")
            kid.expand(generator)

    def __repr__(self):
        return f'<<PamlNode: #kids {len(self.children)}>>'


class ElementNode(PamlNode):
    def __init__(self, tag, classes, elid, attrs, eval_text, text):
        #print(f'New Element Node: {tag}')
        super().__init__()
        self.tag = tag
        self.classes = classes
        self.elid = elid
        self.attrs = attrs
        self.eval_text = eval_text
        self.text = text


    def _expand_attrs(self, generator):
        attrs = self.attrs
        #print('expand attrs:', type(self.attrs), self.attrs)
        if self.classes:
            classes = attrs.get('class', [])
            classes += self.classes
            classes = ' '.join(classes)
            attrs['class'] = classes

        if self.elid:
            attrs['id'] = self.elid

        if not attrs:
            return

        for name in attrs:
            generator.text(f' {name}={repr(str(attrs[name]))} ')

    def expand_text(self, generator):
        #print("expand text", self.text)
        if not self.text:
            return
        if (self.eval_text):
            generator.expr(self.text)
        else:
            generator.text(self.text)

    def expand(self, generator):
        logging.info('Compile <%s> %s', self.tag, self.text)
        generator.text(f'<{self.tag}')
        self._expand_attrs(generator)

        if (not self.children) and (not self.text):
            generator.text('/>\n')
        elif self.text and (not self.children):
            generator.text('>')
            self.expand_text(generator)
            generator.text(f'</{self.tag}>\n')
        else:
            generator.text('>\n')
            self.expand_text(generator)
            self._expand_children(generator)
            generator.text(f'</{self.tag}>\n')
            
    def __repr__(self):
        return f'<<Node: tag {self.tag} text [{self.text}] #kids {len(self.children)}>>'

class ContentNode:
    def __init__(self, text):
        logging.info("New content node: %s", text)
        self.text = text

    def expand(self, generator):
        #print("Context Compile: %s", generator, self.text)
        #print("type generator:", type(generator))
        generator.text(self.text)

    def __repr__(self):
        return f'<<ContentNode: {self.text}>>'

START_RE = re.compile(r'.*:$')

class ExpressionNode(PamlNode):
    def __init__(self, text):
        logging.info("New expr node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        logging.info("Compile: %s", self.text)
        generator.expr(self.text)
        self._expand_children(generator)

class CommandNode(PamlNode):
    def __init__(self, text):
        logging.info("New command node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        logging.info("Compile: %s", self.text)
        generator.code(self.text)

        if START_RE.match(self.text):
            generator.indent()
        self._expand_children(generator)
        if START_RE.match(self.text):
            generator.dedent()
