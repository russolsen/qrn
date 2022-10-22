from pathlib import Path
import logging
import qrn.pipeline as pl
import qrn.components as components
import qrn.converters as converters
import qrn.utils as utils

INCLUDE_DIR = Path('content/_layouts')

from qrn.expander import Expander

def compute_html(ipath, page):
    """Compute the html resulting from expanding ipath."""
    expander = Expander('content/_layouts', ipath, page)
    return expander.expand()

def build_html(context):
    """Build html from the source file."""
    ipath = context['sources'][0]
    page = context['attrs']
    context['text'] = compute_html(ipath, page)
    return context

def write_text(context):
    """Write the text from the context to the output file."""
    opath = context['output']
    text = context['text']
    utils.write_file(text, opath)
    return context

def build_css(context):
    """Create the output css file from the input file."""
    ipath = context['sources'][0]
    opath = context['output']
    converters.sass_to_css(ipath, opath)
    return context

def set_url(context):
    """Set the url in the context based on the output path."""
    opath = context['output']
    attrs = context['attrs']
    attrs['url'] = '/' + str(Path(*opath.parts[1:]))
    return context

def insert_attr_f(name, value):
    """Insert an attribute into the attrs dictionary in the context."""
    def insert_attr(context):
        context['attrs'][name] = value
        return context
    return insert_attr

def debug_f(msg):
    """Return a function that logs pipeline paths with a message"""
    def gen_debug_msg(context):
        sources = context.get('sources', None)
        if sources:
            ipath = sources[0]
        else:
            ipath = 'None'
        opath = context.get('output', 'None')
        logging.debug('%s: ipath %s opath %s', msg, ipath, opath)
        return context
    return gen_debug_msg

is_html_src = components.is_suffix_f('.md', '.html', '.haml')

def sort_by_date(pages):
    pages.sort(key=lambda p: p.get('date', '0000'), reverse=True)

def build_indices():
    """Compute the category and url indices."""
    by_url = {}
    by_category = {}
    all_pages = []

    def index_by_url(context):
        opath = context['output']
        attrs = context['attrs']
        url = attrs['url']
        by_url[url] = attrs
        return context

    def index_by_category(context):
        opath = context['output']
        attrs = context['attrs']
        category = attrs.get('category', 'none')
        pages = by_category.get(category, [])
        pages.append(attrs)
        by_category[category] = pages
        return context

    def collect_page(context):
        all_pages.append(context['attrs'])
        return context

    rule = [
            is_html_src,
            components.to_dependency_f('build', '.html'),
            components.read_attrs,
            set_url,
            collect_page,
            index_by_url,
            index_by_category,
            utils.always(pl.COMPLETE)
            ]

    paths = utils.match_pats('content/*', 'content/**/*')
    pl.build_all([rule, [utils.always(pl.COMPLETE)]], paths)

    sort_by_date(all_pages)

    for category in by_category:
        sort_by_date(by_category[category])

    return all_pages, by_url, by_category

def build_site(site):
    """Build the site, source in content result in build."""
    sources = utils.match_pats('content/**/', 'content/*', 'content/**/*')
    html_inc_files = utils.match_pats('content/_layouts/*', include_all=True)
    css_inc_files = utils.match_pats('context/stylesheets/_*', include_all=True)

    html_rule = [
            is_html_src,
            components.to_dependency_f('build', '.html', html_inc_files),
            components.isoutdated,
            components.print_path_f("Building"),
            components.read_attrs,
            set_url,
            insert_attr_f('site', site),
            build_html,
            debug_f('Writing html'),
            write_text,
            utils.always(pl.COMPLETE)
            ]

    css_rule = [
            components.is_suffix_f('.sass', '.scss'),
            components.to_dependency_f('build', '.css', css_inc_files),
            components.isoutdated,
            debug_f('Generating CSS'),
            build_css,
            utils.always(pl.COMPLETE)
            ]

    dir_rule = [
            components.is_dir,
            components.to_dependency_f('build'),
            debug_f('Create directory'),
            components.create_dir,
            utils.always(pl.COMPLETE)]

    copy_rule = [
            components.to_dependency_f('build'),
            components.isoutdated,
            debug_f('Copy file'),
            components.copy_file,
            utils.always(pl.COMPLETE)]

    rules = [html_rule, css_rule, dir_rule, copy_rule]

    print('build....')
    return pl.build_all(rules, sources)

