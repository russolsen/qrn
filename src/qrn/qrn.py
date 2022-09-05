import sys
import os
import os.path
from functools import reduce, partial
import qrn.utils as utils
from qrn.relative_path import RelativePath
from qrn.utils import pp
from qrn.template import Template
import qrn.converters as converters
import qrn.htapi as htapi
import logging

CachedTemplate = utils.memoize(Template.from_file)

class Site:
    """Overall configuration for the static site."""

    def __init__(self, title, url, category_idx={}):
        self.title = title
        self.url = url
        self.set_category_idx(category_idx)

    def set_category_idx(self, idx):
        self._category_idx = idx
        self.categories = list(idx.keys())
        self.categories.sort()

    def category_idx(self):
        return self._category_idx

    def pages_for_category(self, c, max_n=0):
        pages = self._category_idx[c]
        pages.sort(key=lambda p: p.title)
        if max_n > 0:
            pages = pages[0:max_n]
        return pages

class SourceFile:
    """A generic source file."""

    def __init__(self, site, root, path, out_root):
        self.site = site
        self.in_path = RelativePath.from_path(root, path)
        self.out_path = self.compute_out_path(out_root)
        logging.info(f'SourceFile init: %s', self.in_path)
        self.categories = None

    def compute_out_path(self, out_root):
        return self.in_path.modify(root=out_root)

    def outdated(self):
        ipath = self.in_path.full_path()
        opath = self.out_path.full_path()
        return utils.outdated(ipath, opath)

    def process(self):
        if self.outdated():
            self.do_process()
        return self

    def do_process(self):
        raise Exception('Not implemented')

    def categories(self):
        raise Exception('Not implemented')

    def full_ipath(self):
        return self.in_path.full_path()

    def full_opath(self):
        return self.out_path.full_path()

    def __repr__(self):
        return f'{type(self).__name__}: ({self.in_path} -> {self.out_path})'

class Asset(SourceFile):
    """An asset, a file that just gets copied to the target site."""

    def do_process(self):
        site = self.site
        ipath = self.full_ipath()
        opath = self.full_opath()
        converters.copy_file(ipath, opath)

class SassFile(SourceFile):
    """A sass or scss file. Plain CSS files are just assets"""

    def compute_out_path(self, out_root):
        return self.in_path.modify(root=out_root, suffix='css')

    def do_process(self):
        site = self.site
        ipath = self.full_ipath()
        opath = self.full_opath()
        converters.copy_sass_to_css(ipath, opath)

class Page(SourceFile):
    """A asset that can be transformed into html."""

    def __init__(self, site, root, path, out_root):
        super().__init__(site, root, path, out_root)
        self.attrs = utils.read_header(self.full_ipath())
        for a in self.attrs:
            setattr(self, a, self.attrs[a])
        categories = self.attrs.get('categories', [])
        if isinstance(categories, str):
            categories = categories.split()
        self.categories = categories
 
    def compute_out_path(self, out_root):
        return self.in_path.modify(root=out_root, suffix='html')

    def _read(self):
        path = self.full_ipath()
        logging.debug('Reading body %s', path)
        self.content = utils.read_body(path)
        return self

    def _write(self):
        path = self.full_opath()
        logging.info('Writing %s', self)
        with open(path, 'w') as f:
            f.write(self.content)
        return self

    def _expand(self):
        logging.debug("Expand page %s", self)
        p_template = Template(self.content, self.in_path.name)
        output = self.render_template(p_template)
        self.content = output
        return self
    
    def _layout(self):
        logging.debug("Layout self %s", self)
        path = f'layouts/{self.layout}'
        template = CachedTemplate(path, self.layout)
        output = self.render_template(template)
        self.content = output
        return self

    def render_partial(self, partial_path):
        logging.debug('Render partial %s', partial_path)
        path = f'layouts/{partial_path}'
        partial_template = CachedTemplate(path, partial_path)
        output = partial_template.render(globals(), locals())
        return output

    def list_categories(self):
        return self.site.categories

    def top_n(self, ary, n):
        n = min(len(ary), n)
        return ary[:n]

    def link_to_page(self, page, fmt='html'):
        url = "/" + page.out_path.path()
        if fmt == 'html':
            return htapi.ATx(url, page.title.title()).encode()
        else:
            return f'[{page.title.title()}]({url})'

    def image_tag(self, url):
        return htapi.Img(url).encode()
    
    def link_with_image(self, url, img_src):
        return htapi.AImg(url, img_src).encode()
    
    def link_to(self, url, text):
        return htapi.ATx(url, text).encode()
    
    def render_page(self):
        return self.content

    def render_template(self, t):
        return t.render(globals(), locals())


class MarkdownPage(Page):
    """A page more or less assumed to be in markdown format."""
 
    def do_process(self):
        self._read()
        self._expand()
        self._to_html()
        self._layout()
        self._write()
        return self

    def _to_html(self):
        self.content = converters.md_to_html(self.content)

class TemplatedHtml(Page):
    """An HTML file that needs to be run thru the template filter."""
 
    def do_process(self):
        self._read()
        self._expand()
        self._layout()
        self._write()
        return self

def init_logging(path='log_site.txt', level=logging.INFO, filemode='w'):
    fmt='%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(filename=path, level=level, format=fmt, filemode=filemode)

def scan(directory, pats, exclusions=[], include_dirs=False):
    """Python version of the find command."""

    logging.info('Scan files dir: %s pats %s', directory, pats)
    paths = set()
    for g in pats:
        these_paths = utils.xglob(directory, g)
        paths = paths.union(set(these_paths))

    result = []
    for p in paths:
        if utils.globs(exclusions, p):
            continue
        result.append(p)
    
    if not include_dirs:
        result = filter(partial(utils.is_file, directory), result)
    return result

def sort_by_date(pages, reverse=True):
    pages.sort(key=(lambda p: p.created_at), reverse=reverse)
    return pages

def tap(desc, page):
    print(f"\n\nPage: {desc}")
    print(f"Title: {page.title}")
    print(f"Text: {page.content[0:100]}")
    return page

def index_categories(idx, page):
    categories = page.categories
    logging.debug(f'Index categories: page %s cates: %s', page, page.categories)
    if categories:
        for c in categories:
            page_list = idx.get(c, [])
            page_list.append(page)
            idx[c] = page_list
    return idx

def build_category_index(files):
    logging.info('Building category index %s', files)
    idx = reduce(index_categories, files, {})
    for c in idx:
        cpages = idx[c]
        cpages = sort_by_date(cpages)
        idx[c] = cpages
    return idx

def sourcefile_for(site, in_root, path, out_root):
    """Return an appropriate SourceFile instance for the path."""
    suffix = utils.get_suffix(path)
    if suffix == 'md':
        return MarkdownPage(site, in_root, path, out_root)
    if suffix == 'thtml':
        return TemplatedHtml(site, in_root, path, out_root)
    if (suffix == 'sass') or (suffix == 'scss'):
        return SassFile(site, in_root, path, out_root)
    return Asset(site, in_root, path, out_root)

def process_static_files(site, in_dir, out_dir, paths):
    """Takes a list of src paths and builds the appropriate assets."""

    # Turn all the paths into Files
    files = utils.doall(
            lambda p: sourcefile_for(site, in_dir, p, out_dir),
            paths)

    # Build the category index for all the files. We
    # need the index when we do the page processing.

    idx = build_category_index(files)
    site.set_category_idx(idx)

    # Now do the page processing.

    return utils.doall(lambda f: f.process(), files)


def process_dynamic_files(xform_f, site, page, items):
    """Generate dynamic pages, pased on path, one for each item."""
    for i in items:
        logging.info(f'Index: %s', i)
        page = xform_f(i, page)
        page.process()
