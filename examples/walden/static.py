import logging
from qrn.qrn import build_indices, build_site
import qrn.rss as rss
from qrn.utils import pp

fmt='%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename='static.log', level=logging.DEBUG, format=fmt, filemode='w')

def main():
    # Step 1,  index all of the pages. We need the indices for
    # related and recent articles and to build the atom feed.

    site = build_indices()

    site['title'] = 'Technology! As If People Mattered'
    site['subtitle'] = 'sub title'
    site['url'] = 'http://russolsen.com'

    # Step 2, create all the directories and pages.

    build_site(site)

#import cProfile
#cProfile.run('main()')

main()
