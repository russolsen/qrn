import logging
from pathlib import Path
import xml.etree.ElementTree as ET
import qrn.utils as utils
import qrn.epy as epy
import qrn.paml as paml
import qrn.converters as converters
import qrn.rss as rss

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

    def atom_xml(self, pages):
        url = self.page['url']
        site = self.page['site']
        result = rss.to_rss_str(self.page['site'], url, pages)
        return result

    def related(self, n=3):
        category = self.page.get('category', None)
        if not category:
            return []
        else:
            site = self.page['site']
            by_category = site['by_category']
            pages = by_category[category]
            return list(self.__filter_pages(pages, n))

    def articles(self, n=999999):
        site = self.page['site']
        all_articles = site['articles']
        return self.__filter_pages(all_articles, n)

    def sort_by(self, alist, fieldname, default=None, reverse=False):
        result = alist.copy()
        result.sort(
                key=lambda a: a.get(fieldname, default),
                reverse=reverse)
        logging.debug("sorted by %s: %s", fieldname, result)
        return result

    def anchor_for_page(self, page, text=None):
        url = page['url']
        if not text:
            text = page.get('title', 'No title')
        return self.__make_anchor(url, text)

    def find_page_by_id(self, identifier):
        site = self.page['site']
        all_pages = site['all_pages']
        return next((p for p in all_pages if p.get('id', None) ==  identifier), None)

    def find_pages(self, *kvs):
        if (len(kvs) % 2) == 1:
            logging.error("Odd number of value: %s", nvs)
            raise Exception("find_pages: You must supply a value for each attribute.")
        site = self.page['site']
        pages = site['all_pages']
        pairs = utils.partition(kvs, 2)
        for pair in pairs:
            logging.debug('pair: %s', pair)
            name = pair[0]
            value = pair[1]
            pages = list(filter(lambda page: page.get(name,None) == value, pages))
            logging.debug("filtered pages: %s", len(pages))
        return list(pages)

    def find_page(self, *kvs):
        pages = self.find_pages(*kvs)
        if pages:
            return pages[0]
        return []

    def find_page_url(self, *kvs):
        page = self.find_page(*kvs)
        if not page:
            logging.error("Page not found: attribute %s value %s", name, value)
            raise Exception(f'Page not found: {value}')
        return page['url']

    def url_for_id(self, ident):
        return self.find_page_url('id', ident);

    def anchor_for_id(self, ident, text=None):
        page = self.find_page_by_id(ident)
        if not page:
            logging.error("Page id not found: %s", ident)
            raise Exception(f'Page not found: {ident}')
        return self.anchor_for_page(page, text)

    def include_relative(self, path):
        directory = self.path.parent
        real_path = Path(directory, path)
        return self.include(real_path, full_path=True)

    def add_locals(self, env):
        env['page'] = self.page
        env['include'] = self.include
        env['include_relative'] = self.include_relative
        env['related'] = self.related
        env['articles'] = self.articles
        env['find_page'] = self.find_page
        env['find_pages'] = self.find_pages
        env['sort_by'] = self.sort_by
        env['anchor_for_page'] = self.anchor_for_page
        env['anchor_for_id'] = self.anchor_for_id
        env['find_page_url'] = self.find_page_url
        env['url_for_id'] = self.url_for_id
        env['atom_xml'] = self.atom_xml
        env['self'] = self

class Expander(Helpers):
    code_cache = {}

    def __init__(self, inc_dir, path, page):
        self.inc_dir = inc_dir
        self.path = path
        self.page = page
     
    def include(self, path, full_path=False):
        if not full_path:
            path = Path(self.inc_dir, path)
        page = utils.read_header(path)
        body = utils.read_body(path)
        return self.__do_expand(path, body, page) 

    def expand(self):
        if self.page.get('layout', None):
            logging.debug('Page %s, applying layout %s', self.path, self.page['layout'])
            return self.include(self.page['layout'])
        else:
            logging.debug('No layout for page %s.', self.path)
            body = utils.read_body(self.path)
            return self.__do_expand(self.path, body, self.page)

    def __do_expand(self, path, text, env):
        env = env.copy()
        self.add_locals(env)
        return self.__eval_text(path, text, env)

    def __eval_text(self, path, text, env):
        if path.suffix == '.md':
            code = epy.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
            content = converters.md_to_html(content)
        elif path.suffix in ['.xml', '.html']:
            code = epy.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
        elif path.suffix == '.haml':
            code = paml.template_from_text(text, path)
            content = utils.exec_prog_output(code, loc=env)
        else:
            raise(Exception(f'Dont know what to do with {path}'))

        return content
