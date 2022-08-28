import html

# Hyper text API

class Element:
    """A generic HTML element."""

    def __init__(self, tag, attrs=None, *body_elements):
        self.tag = tag
        self.attrs = attrs
        self.body = []
        self.add(*body_elements)
        #print(f'attrs: {self.attrs} body {self.body}')

    def __repr__(self):
        return f'{self.tag} attrs: {self.attrs} body {self.body}'

    def add(self, *children):
        """Add child elements to this element."""
        for c in children:
            self.body.append(c)

    def encode(self):
        """Encode this element as a string."""

        if (self.attrs == None) and (self.body == None):
            return f'<{self.tag}/>'

        result = f'<{self.tag} '
        result += self.encode_attrs()
        result += '>'
        result += self.encode_body()
        result += f'</{self.tag}>'
        return result

    def encode_attr(self, name, value):
        return f'{name}="{value}"'

    def encode_body(self):
        #print(f'{self.tag}: Encode body: {self.body}')
        result = ''
        for b in self.body:
            result += b.encode()
            result += '\n'
        return result

    def encode_attrs(self):
        if not self.attrs:
            return ''
        names = self.attrs.keys()
        strings = map(lambda n: self.encode_attr(n, self.attrs[n]), names)
        return ' '.join(strings)

class Div(Element):
    """A <div> element."""

    def __init__(self, attrs=None, *body_elements):
         super().__init__('div', attrs, *body_elements)

class Ul(Element):
    """A <ul> element."""

    def __init__(self, attrs=None, *body_elements):
         super().__init__('ul', attrs, *body_elements)

class Li(Element):
    """A <li> element."""

    def __init__(self, attrs=None, *body_elements):
         super().__init__('li', attrs, *body_elements)


class A(Element):
    """An anchor element."""

    def __init__(self, attrs=None, *body_elements):
         super().__init__('a', attrs, *body_elements)
    
def ATx(url, text):
    """An anchor that contains some text."""

    return A({'href': url}, Tx(text))

def LiA(href, text):
    """A list item that contains some text."""

    return LI(A.simple(href, text))

class Img(Element):
    """An image."""

    def __init__(self, src, clz=None):
        attrs = {'src': src}
        if(clz):
            attrs['class'] =  clz
        super().__init__('img', attrs)

def AImg(url, img_src):
    """An anchor that contains an image."""
    return A({'href': url}, Img(img_src))

class Tx:
    """A text element."""
    def __init__(self, text):
        self.text = text

    def encode(self):
        return html.escape(self.text)

def test():
    container = Div({'class': 'container'})
    
    logo = Div({'class': 'sixteen columns menu'}, 
            Img("https://pypi.org/static/images/logo-small.95de8436.svg", "logo"))
    container.add(logo)
    
    item_ul = Ul()
    for i in range(5):
        s = f'Yahoo link {i}'
        a = ATx('http://yahoo.com', s)
        li = Li(None, a)
        item_ul.add(li)
    
    menu = Div({'class': 'sixteen columns menu'}, item_ul)
    container.add(menu)
            
    print(container.encode())
