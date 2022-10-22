import logging
from pathlib import Path
import qrn.utils as utils
import qrn.epy as epy
import qrn.paml as paml
import qrn.converters as converters
import xml.etree.ElementTree as ET

class Helpers:
    def __filter_pages(self, pages, n):
        url = self.page['url']
        candidates = pages[:n+1]
        list(filter(lambda p: p['url'] != url, candidates))
        return candidates[:n]

    def __make_anchor(self, url, text):
        a = ET.Element('a')
        a.attrib['href'] = url
        a.text = text
        return ET.tostring(a, method='html', encoding='unicode')

    def related(self, n=3):
        logging.info('related, page: %s', self.page.keys())
        category = self.page.get('category', None)
        if not category:
            return []
        else:
            site = self.page['site']
            by_category = site['by_category']
            pages = by_category[category]
            return self.__filter_pages(pages, n)

    def recent(self, n=3):
        site = self.page['site']
        all_pages = site['all_pages']
        return self.__filter_pages(all_pages, n)

    def anchor_for_page(self, page, text=None):
        url = page['url']
        if not text:
            text = page.get('title', 'No title')
        return self.__make_anchor(url, text)

    def find_page_by_id(self, identifier):
        site = self.page['site']
        all_pages = site['all_pages']
        return next((p for p in all_pages if p.get('id', None) ==  identifier), None)

    def anchor_for_id(self, ident, text=None):
        page = self.find_page_by_id(ident)
        if not page:
            raise Exception(f'Page not found: {title}')
        return self.anchor_for_page(page, text)

class Expander(Helpers):
    def __init__(self, inc_dir, path, page):
        self.inc_dir = inc_dir
        self.path = path
        self.page = page
     
    def __do_expand(self, path, text, env):
        env = env.copy()
        env['include'] = self.include
        env['related'] = self.related
        env['recent'] = self.recent
        env['anchor_for_page'] = self.anchor_for_page
        env['anchor_for_id'] = self.anchor_for_id
        env['self'] = self
        return self.__eval_text(path, text, env)

    def include(self, path, full_path=False):
        if not full_path:
            path = Path(self.inc_dir, path)
        page = utils.read_header(path)
        body = utils.read_body(path)
        return self.__do_expand(path, body, page) 

    def expand(self):
        if self.page.get('layout', None):
            return self.include(self.page['layout'])
        else:
            body = utils.read_body(self.path)
            return self.__do_expand(self.path, body, self.page)
            #return self.include(self.path, full_path=True)

    def __eval_text(self, path, text, env):
        if path.suffix == '.md':
            code = epy.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
            content = converters.md_to_html(content)
        elif path.suffix == '.html':
            code = epy.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
        elif path.suffix == '.haml':
            code = paml.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
        else:
            raise(Exception(f'Dont know what to do with {path}'))

        return content
