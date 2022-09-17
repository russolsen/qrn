import logging
import qrn.utils as utils
import qrn.converters as converters
import qrn.htapi as htapi
from qrn.relative_path import RelativePath 
from qrn.epy import EPyCompiler
from qrn.paml import PamlCompiler

def top_n(ary, n):
    n = min(len(ary), n)
    return ary[:n]
  
def link_to_page(page, fmt='html'):
    url = "/" + page.out_path.path()
    if fmt == 'html':
        return htapi.ATx(url, page.title).encode()
    else:
        return f'[{page.title}]({url})'
  
def image_tag(url):
    return htapi.Img(url).encode()
  
def link_with_image(url, img_src):
    return htapi.AImg(url, img_src).encode()
  
def link_to(url, text):
    return htapi.ATx(url, text).encode()
 
def sort_by_date(pages, reverse=True):
    pages.sort(key=(lambda p: p.created_at), reverse=reverse)
    return pages

class Asset:
    def __init__(self, site, factory, path):
        self.site = site
        self.factory = factory
        self.path = path
        self.in_path = RelativePath.from_path(site.root, path)
        self.out_path = RelativePath.from_path(site.out_root, path)
        self.fmt = utils.get_suffix(path)
        self.name = utils.get_filename(path)
        self.attrs ={}
        self.prepare()
        site.add_asset(self)

    def prepare(self):
        pass

    def process(self):
        if self.is_outdated():
            logging.info("%s out of date, processing.", self)
            print(f'Processing {self.name}.')
            self.do_process()
        else:
            logging.info("%s is up to date.", self)

    def do_process(self):
        pass

    def compute_content(self, locs=None):
        return "CONTENT"

    def is_outdated(self):
        ipath = self.in_path.full_path()
        opath = self.out_path.full_path()
        return utils.outdated(ipath, opath)
    
    def full_ipath(self):
        return self.in_path.full_path()
    
    def full_opath(self):
        return self.out_path.full_path()

    def get_layout(self):
        return self.attrs.get('layout', None)

    def add_to_index(self, asset_index):
        asset_index.add(self, *self.categories)


    # Anything in self.attrs becomes a field on the object.
    # Handy because this means that attrs stored in the asset headers
    # magically become fields on the Asset instance.
    def __getattr__(self, name):
        if name in self.attrs:
            return self.attrs[name]
        cname = type(self).__name__
        raise AttributeError(f"'{cname}' object has no attribute '{name}'")

    def __repr__(self):
        return f'{type(self).__name__}: {self.path}'

class TemplatedAsset(Asset):
    """And asset that had a header is is run thru the EPy templating."""

    def __init__(self, cclass, site, factory, path):
        self.compiler_class = cclass
        super().__init__(site, factory, path)

    def convert(self, content):
        return content

    def do_process(self):
        content = self.compute_content()
        opath = self.full_opath()
        utils.write_file(content, opath, "w")

    def compute_content(self, locs=None):
        # locs contains the local environment, used when we
        # do template evaluation. We wither start with the
        # passed in or use the current one. Either
        # way we make a copy so that we won't pollute the env
        # of other assets.

        env = locs
        if env:
            env = env.copy()
        else:
            env = locals()
            env['page'] = self
 
        # This is the function that is called inside of
        # the templates to include another asset.

        def include(path):
            logging.info("Including page %s.", path)
            asset = self.factory.asset_for_path(path)
            my_env = env.copy()
            my_env['included_page'] = asset
            text = asset.compute_content(my_env)
            logging.debug("Included text %s.", text)
            return text

        # Make sure we have a reference to the current page and
        # the include function in the env.

        env['include'] = include

        # Compute the evaluated content. Note we use locs in the
        # epy compilation.
        ipath = self.full_ipath()
        content = utils.read_body(ipath)
        content = self.compiler_class.evaluate(content, self.path, globals(), env)
        content = self.convert(content)

        # If a layout is speficied, use that.

        if self.get_layout():
            lo = self.factory.asset_for_path(self.get_layout())
            env['layout_page'] = lo
            env['content'] = content
            content = lo.compute_content(env)
        return content

class MarkdownAsset(TemplatedAsset):
    """Markdown page, has a header and does templating, possibly with a layout"""

    def __init__(self, site, factory, path):
        super().__init__(EPyCompiler, site, factory, path)

    def prepare(self):
        ipath = self.full_ipath()
        self.attrs = utils.read_header(ipath)
        self.out_path = self.out_path.modify(suffix="html")

    def convert(self, content):
        return converters.md_to_html(content)

class HTMLAsset(TemplatedAsset):
    """HTML page, has a header and does templating, possibly with a layout"""

    def __init__(self, site, factory, path):
        super().__init__(EPyCompiler, site, factory, path)

    def prepare(self):
        ipath = self.full_ipath()
        self.attrs = utils.read_header(ipath)

class HAMLAsset(TemplatedAsset):
    """HAML page, has a header and does templating, possibly with a layout."""

    def __init__(self, site, factory, path):
        super().__init__(PamlCompiler, site, factory, path)

    def prepare(self):
        ipath = self.full_ipath()
        self.attrs = utils.read_header(ipath)
        self.out_path = self.out_path.modify(suffix="html")

class OtherAsset(Asset):
    """Generic asset, just gets copied."""

    def do_process(self):
        ipath = self.full_ipath()
        opath = self.full_opath()
        converters.copy_file(ipath, opath)

class SassAsset(Asset):
    """SASS/SCSS asset, gets processed by sass."""

    def prepare(self):
        self.out_path = self.out_path.modify(suffix="css")

    def do_process(self):
        ipath = self.full_ipath()
        opath = self.full_opath()
        return converters.sass_to_css(ipath, opath)

class AssetFactory:
    """Maintains a registry of fmts -> asset classes, makes assets from paths."""

    def __init__(self, site, default_asset_class = OtherAsset):
        self.site = site
        self.default_asset_class = default_asset_class
        self.fmt_to_class = {}

    def add_asset_class(self, fmt, clz):
        self.fmt_to_class[fmt] = clz

    def asset_class_for_fmt(self, fmt):
        return self.fmt_to_class.get(fmt, self.default_asset_class)

    def asset_for_path(self, path):
        fmt = utils.get_suffix(path)
        clz = self.asset_class_for_fmt(fmt)
        return clz(self.site, self, path)

    def assets_for_paths(self, paths):
        return map(self.asset_for_path, paths)

def standard_asset_factory(site):
    asset_factory = AssetFactory(site)
    asset_factory.add_asset_class('md', MarkdownAsset)
    asset_factory.add_asset_class('html', HTMLAsset)
    asset_factory.add_asset_class('haml', HAMLAsset)
    asset_factory.add_asset_class('sass', SassAsset)
    asset_factory.add_asset_class('scss', SassAsset)
    return asset_factory

class AssetIndex:
    """Track assets by their categories."""

    def __init__(self):
        self.idx = {}
        self.assets = []

    def add(self, asset, *categories):
        self.assets.append(asset)
        for c in categories:
            assets = self.idx.get(c, set())
            assets.add(asset)
            self.idx[c] = assets

    def newest_assets(self, n):
        return self.assets[0:n]

    def assets_in_category(self, category):
        return self.idx.get(category, set())

    def categories(self):
        return self.idx.keys()

    def __repr__(self):
        return f'(AssetIndex): {self.idx.keys()}'

class Site:
    def __init__(self, title, url, root, out_root):
        self.title = title
        self.url = url
        self.root = root
        self.out_root = out_root
        self.index = AssetIndex()

    def add_asset(self, asset):
        categories = asset.attrs.get('categories', [])
        self.index.add(asset, *categories)

    def __repr__(self):
        return f'Site: {self.title} {self.url} {self.index}'
