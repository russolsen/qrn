"""Opinionated static site generator."""

from pathlib import Path
import logging
import datetime
import qrn.pipeline as pl
import qrn.components as components
import qrn.converters as converters
import qrn.rss as rss
import qrn.utils as utils

from qrn.expander import Expander

def compute_text(ipath, page):
    """Compute the html resulting from expanding ipath."""
    expander = Expander('src/_layouts', ipath, page)
    return expander.expand()

def build_html(context):
    """Build html from the source file."""
    ipath = context['sources'][0]
    page = context['attrs']
    context['text'] = compute_text(ipath, page)
    return context

def build_xml(context):
    """Build xml from the source file."""
    ipath = context['sources'][0]
    page = context['attrs']
    context['text'] = compute_text(ipath, page)
    return context

def write_text(context):
    """Write the text from the context to the output file."""
    opath = context['output']
    text = context['text']
    logging.debug('Writing text to %s', opath)
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

def insert_attr_f(*args):
    """Insert an attribute into the attrs dictionary in the context."""
    extra_keys = args[:-2]
    key = args[-2]
    value = args[-1]
    def insert_attr(context):
        dictionary = context
        for k in extra_keys:
            dictionary = dictionary[k]
        dictionary[key] = value
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

EARLY = datetime.date(2004,1,1)

def sort_by_date(pages):
    pages.sort(key=lambda p: p.get('date', EARLY), reverse=True)

def sort_by(pages, fieldname, default=None, reverse=False):
    return pages.sort(key=lambda p: p.get(fieldname, default), reverse=reverse)

def build_indices(output_dir='build'):
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
            components.to_dependency_f(output_dir, '.html'),
            components.read_attrs,
            components.ispublished,
            set_url,
            collect_page,
            index_by_url,
            index_by_category,
            utils.always(pl.COMPLETE)
            ]

    paths = utils.match_pats('src/*', 'src/**/*')
    pl.build_all([rule, [utils.always(pl.COMPLETE)]], paths)

    sort_by(all_pages, 'date', EARLY, True)
    articles = list(filter(lambda p: p.get('kind', '') == 'article', all_pages))

    for category in by_category:
        #sort_by_date(by_category[category])
        sort_by(by_category[category], 'date', EARLY, True)

    return utils.EasyDict({
        'all_pages': all_pages,
        'articles': articles,
        'by_url': by_url,
        'by_category': by_category})

def build_site(site, output_dir='build'):
    """Build the site, source in src result in build."""
    sources = utils.match_pats('src/**/', 'src/*', 'src/**/*')
    html_inc_files = utils.match_pats('src/_layouts/*', include_all=True)
    css_inc_files = utils.match_pats('src/**/_*.scss', 'src/**/_*.css', include_all=True)

    logging.debug('Sources: %s', sources)
    logging.debug('HTML INC: %s', html_inc_files)
    logging.debug('CSS INC: %s', css_inc_files)

    html_rule = [
            is_html_src,
            components.to_dependency_f(output_dir, '.html', html_inc_files),
            components.isoutdated,
            components.read_attrs,
            components.ispublished,
            components.print_path_f("Building from HTML"),
            set_url,
            insert_attr_f('attrs', 'site', site),
            build_html,
            debug_f('Writing html'),
            write_text,
            utils.always(pl.COMPLETE)
            ]

    xml_rule = [
            components.is_suffix_f('.xml'),
            components.to_dependency_f(output_dir),
            components.read_attrs,
            components.print_path_f("Building from XML"),
            insert_attr_f('attrs', 'site', site),
            set_url,
            build_xml,
            write_text,
            utils.always(pl.COMPLETE)
            ]

    css_rule = [
            components.is_suffix_f('.sass', '.scss'),
            components.to_dependency_f(output_dir, '.css', css_inc_files),
            components.isoutdated,
            components.print_path_f("Building SASS/SCSS"),
            build_css,
            utils.always(pl.COMPLETE)
            ]

    dir_rule = [
            components.is_dir,
            components.to_dependency_f(output_dir),
            debug_f('Create directory'),
            components.create_dir,
            utils.always(pl.COMPLETE)]

    copy_rule = [
            components.to_dependency_f(output_dir),
            components.isoutdated,
            components.print_path_f("Copying"),
            debug_f('Copy file'),
            components.copy_file,
            utils.always(pl.COMPLETE)]

    rules = [xml_rule, html_rule, css_rule, dir_rule, copy_rule]

    print('build....')
    return pl.build_all(rules, sources)
