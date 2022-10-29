import xml.etree.ElementTree as ET
from io import StringIO
import uuid
import datetime
import qrn.utils as utils

def element(tag, text=None, attrs=None):
    result = ET.Element(tag)
    if text:
        result.text = text
    if attrs:
        result.attrib.update(attrs)
    return result

def time_element(tag, t):
    stime = utils.format_rfc822(t)
    return element(tag, stime)

def full_url(site, page):
    return f'{site["url"]}{page["url"]}'

def guid_element(site, page):
    attrs = {'isPermaLink': 'false'}
    return element('guid', full_url(site,page), attrs)
    
def append_page_item(el, site, page):
    if 'article' != page.get('kind', 'none'):
        return
    item = ET.Element('item')
    item.append(element('title', page['title']))
    item.append(element('description', page.get('title', '')))
    item.append(time_element('pubDate', page['date']))
    item.append(element('link', full_url(site, page)))
    item.append(guid_element(site, page))
    #<guid isPermaLink="false">https://news.ycombinator.com/item?id=33335278</guid>
    el.append(item)

def channel_link_element(site, feed_url):
    attrs = {}
    attrs['rel'] = 'self'
    attrs['type'] = 'application/rss+xml'
    attrs['href'] = f'{site["url"]}{feed_url}'
    return element('{http://www.w3.org/2005/Atom}link', None, attrs)

def to_rss(site, url, pages):
    ET.register_namespace('atom',  'http://www.w3.org/2005/Atom')
    rss = ET.Element('rss')
    rss.attrib['version'] = '2.0'

    channel = ET.Element('channel')
    rss.append(channel)

    channel.append(element('title', site['title']))
    channel.append(element('description', site.get('description', 'None')))
    channel.append(element('generator', 'https://github.com/russolsen/qrn'))
    channel.append(element('link', f'{site["url"]}{url}'))
    channel.append(time_element('pubDate', datetime.datetime.now()))
    channel.append(channel_link_element(site, url))

    for page in pages:
        append_page_item(channel, site, page)

    tree = ET.ElementTree(rss)
    return tree

def write_rss(rss_tree, ofile):
    return rss_tree.write(
            ofile,
            encoding='Unicode', 
            method='xml', 
            xml_declaration=True)

def to_rss_str(site, url, pages):
    tree = to_rss(site, url, pages)
    f  = StringIO()
    write_rss(tree, f)
    f.seek(0)
    result = f.read()
    f.close()
    return result
