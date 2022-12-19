import re
import logging

class PamlNode:
    def __init__(self):
        self.children = []

    def add_child(self, kid):
        self.children.append(kid)

    def add_all(self, kids):
        logging.debug("Add all: %s", kids)
        for k in kids:
            self.add_child(k)

    def _expand_children(self, generator):
        result = ''
        for kid in self.children:
            kid.expand(generator)

    def __repr__(self):
        return f'<<PamlNode: #kids {len(self.children)}>>'


class ElementNode(PamlNode):
    def __init__(self, tag, classes, elid, attrs, eval_text, text):
        super().__init__()
        self.tag = tag
        self.classes = classes
        self.elid = elid
        self.attrs = attrs
        self.eval_text = eval_text
        self.text = text

    def _expand_attrs(self, generator):
        attrs = self.attrs
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
        if not self.text:
            return
        if (self.eval_text):
            generator.expr(self.text)
        else:
            generator.text(self.text)

    def expand(self, generator):
        logging.debug('Compile <%s> %s', self.tag, self.text)
        generator.text(f'<{self.tag}')
        self._expand_attrs(generator)

        if (not self.children) and (not self.text):
            generator.text('/> ')
        elif self.text and (not self.children):
            generator.text('>')
            self.expand_text(generator)
            generator.text(f'</{self.tag}> ')
        else:
            generator.text('>')
            self.expand_text(generator)
            self._expand_children(generator)
            generator.text(f'</{self.tag}> ')
            
    def __repr__(self):
        return f'<<Node: tag {self.tag} text [{self.text}] #kids {len(self.children)}>>'

class ContentNode(PamlNode):
    def __init__(self, text):
        logging.debug("New content node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        if self.text:
            generator.text(self.text)
            generator.text('\n')
        self._expand_children(generator)

    def __repr__(self):
        return f'<<ContentNode: {self.text}>>'

START_RE = re.compile(r'.*:$')

class ExpressionNode(PamlNode):
    def __init__(self, text):
        logging.debug("New expr node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        logging.debug("Compile: %s", self.text)
        generator.expr(self.text)
        self._expand_children(generator)

class CommentNode(PamlNode):
    def __init__(self, text):
        logging.debug("New comment node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        logging.debug("Compile comment: %s", self.text)
        generator.text('<!-- ')
        generator.text(self.text)
        self._expand_children(generator)
        generator.text(' -->\n')

class CommandNode(PamlNode):
    def __init__(self, text):
        logging.debug("New command node: %s", text)
        super().__init__()
        self.text = text

    def expand(self, generator):
        logging.debug("Compile command: %s", self.text)
        generator.code(self.text)

        if START_RE.match(self.text):
            generator.indent()
        self._expand_children(generator)
        if START_RE.match(self.text):
            generator.dedent()
