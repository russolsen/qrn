import sys
import os
import os.path
from functools import reduce, partial
import qrn.utils as utils
from qrn.utils import pp
from qrn.template import Template
import qrn.converters as converters
import qrn.htapi as htapi
from qrn.log import *

CachedTemplate = utils.memoize(Template.from_file)

class Site:
    """Overall configuration for the static site."""

    def __init__(self, title, url, src_dir, dst_dir, category_idx={}):
        self.title = title
        self.url = url
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.set_category_idx(category_idx)

    def set_category_idx(self, idx):
        self._category_idx = idx
        self.categories = list(idx.keys())
        self.categories.sort()

    def category_idx(self):
        return self._category_idx

    def pages_for_category(self, c, max_n=0):
        #log("Pages for category", c)
        pages = self._category_idx[c]
        pages.sort(key=lambda p: p.title)
        if max_n > 0:
            pages = pages[0:max_n]
        return pages

class SourceFile:
    """A generic source file."""

    def __init__(self, site, ipath, ofmt=None):
        self.site = site
        self.ipath = ipath
        [d, n, s] = utils.split_path(ipath)
        self.path_dir = d
        self.name = n
        self.fmt = s
        self.ofmt = ofmt or s
        log(f'SourceFile init: {self.path_dir} {self.name} {self.fmt}')
        self.categories = None

    def outdated(self):
        ipath = self.full_ipath()
        opath = self.full_opath()
        return utils.outdated(ipath, opath)

    def process(self):
        if self.outdated():
            print(f"processing {self}")
            self.do_process()

    def do_process(self):
        raise Exception('Not implemented')

    def categories(self):
        raise Exception('Not implemented')

    def full_ipath(self):
        return f'{self.site.src_dir}/{self.ipath}'

    def full_opath(self):
        result = f'{self.site.dst_dir}/{self.opath()}'
        return result

    def opath(self):
        result = f'/{self.path_dir}/{self.name}.{self.ofmt}'
        return result

    def __repr__(self):
        return f'{type(self).__name__}: ({self.path_dir} {self.name} {self.fmt})'

class Asset(SourceFile):
    """An asset, a file that just gets copied to the target site."""

    def do_process(self):
        site = self.site
        ipath = self.full_ipath()
        opath = self.full_opath()
        converters.copy_file(ipath, opath)

class SassFile(SourceFile):
    """A sass or scss file. Plain CSS files are just assets"""

    def __init__(self, site, ipath):
        super().__init__(site, ipath, 'css')

    def do_process(self):
        site = self.site
        ipath = self.full_ipath()
        opath = self.full_opath()
        converters.copy_sass_to_css(ipath, opath)


class Page(SourceFile):
    """A page, more or less assumed to be in markdown format."""

    def __init__(self, site, ipath):
        super().__init__(site, ipath, 'html')
        log('Reading', self.site.src_dir,  self.full_ipath())
        self.attrs = utils.read_header(self.full_ipath())
        for a in self.attrs:
            setattr(self, a, self.attrs[a])
        if 'tags' in self.attrs:
            self.attrs['tags'] = self.attrs['tags'].split()
        else:
            self.attrs['tags'] = []
 
    def do_process(self):
        self._read()
        self._expand()
        self._to_html()
        self._layout()
        self._write()
        return self

    def _to_html(self):
        self.content = converters.md_to_html(self.content)

    def _read(self):
        path = self.full_ipath()
        log('Reading body', path)
        self.content = utils.read_body(path)
        return self

    def _write(self):
        path = self.full_opath()
        log('Writing', self.name, path)
        with open(path, 'w') as f:
            f.write(self.content)
        return self

    def categories(self):
        return self.attrs['tags']

    def _expand(self):
        log("Expand page", self.name)
        p_template = Template(self.content, self.name)
        output = self.render_template(p_template)
        self.content = output
        return self
    
    def _layout(self):
        log("Layout self", self.name)
        path = f'{self.site.src_dir}/{self.layout}'
        template = CachedTemplate(path, self.layout)
        output = self.render_template(template)
        self.content = output
        return self

    def render_partial(self, partial_path):
        log('Render partial', partial_path)
        path = f'{self.site.src_dir}/{partial_path}'
        partial_template = CachedTemplate(path, partial_path)
        output = partial_template.render(globals(), locals())
        return output

    def list_categories(self):
        return self.site.categories

    def top_n(self, ary, n):
        n = min(len(ary), n)
        return ary[:n]

    def link_to(self, *args):
        return f'Link to: {args}'

    def link_to_page(self, page, fmt='html'):
        #log("link to page", page)
        url = page.opath()
        if fmt == 'html':
            return htapi.ATx(url, page.title).encode()
        else:
            return f'[{title}]({url})'

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

def scan_files(directory, pats, exclusions=[]):
    """Python version of the find command."""

    log('Scan files', directory, pats)
    paths = set()
    for g in pats:
        these_paths = utils.xglob(directory, g)
        paths = paths.union(set(these_paths))

    result = []
    for p in paths:
        if utils.globs(exclusions, p):
            continue
        result.append(p)

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
    if categories:
        for c in categories:
            page_list = idx.get(c, [])
            page_list.append(page)
            idx[c] = page_list
    return idx

def build_category_index(files):
    log('Building category index')
    idx = reduce(index_categories, files, {})
    for c in idx:
        cpages = idx[c]
        cpages = sort_by_date(cpages)
        idx[c] = cpages
    return idx

def sourcefile_for(site, path):
    """Return an appropriate SourceFile instance for the path."""
    suffix = utils.get_suffix(path)
    if suffix == 'md':
        return Page(site, path)
    if (suffix == 'sass') or (suffix == 'scss'):
        return SassFile(site, path)
    return Asset(site, path)

#def process(site, path):
#    sourcefile_forped = wrap(site, path)
#    return sourcefile_forped.process()

def process_static_files(site, paths):
    """Takes a list of src paths and builds the appropriate assets."""

    # Turn all the paths into Files
    files = utils.doall(partial(sourcefile_for, site), paths)

    # Build the category index for all the files. We
    # need the index when we do the page processing.

    idx = build_category_index(files)
    site.set_category_idx(idx)

    # Now do the page processing.

    return utils.doall(lambda f: f.process(), files)

def process_dynamic_file(xform_f, site, path, items):
    """Generate dynamic pages, pased on path, one for each item."""
    for i in items:
        page = sourcefile_for(site, path)
        page = xform_f(i, page)
        page.process()
