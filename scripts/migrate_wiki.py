#!/usr/bin/env python

import urllib
from lxml import etree
from pprint import pprint

parser = etree.HTMLParser()

def get_namespaces():
    """Return the list of namespaces.

    Get the Special:AllPages page and extract the full list of
    namespaces from it.

    """

    print 'Getting namespaces'
    tree = etree.parse('http://lesswrong.wikia.com/wiki/Special:AllPages', parser)
    options = tree.xpath('//select[@id="namespace"]/option')
    namespaces = [option.get('value') for option in options]
    pprint(namespaces)
    return namespaces


def get_all_pages_for_namespace(ns):
    """Return the list of wiki pages for the specified namespace.

    Get the Special:AllPages page for the specified namespace and
    extract the list of wiki pages from it.

    """

    print 'Getting pages in namespace %s' % ns
    url = 'http://lesswrong.wikia.com/index.php?title=Special:AllPages&from=&to=&namespace=%s' % ns
    tree = etree.parse(url, parser)
    pages = tree.xpath('//table[2]//a[@title]')
    page_names = [page.get('title') for page in pages]
    pprint(page_names)
    return page_names


def get_export(pages_param, out_filename):
    """Send the POST export request and save the XML export response.

    Send a POST to the export page of the wiki requesting an export of
    the specified pages.  The post specifies that templates should be
    included and also that all revisions should be included.  The
    returned XML export is saved to the specified file.

    """

    url = 'http://lesswrong.wikia.com/index.php?title=Special:Export&action=submit'
    data = urllib.urlencode({'catname': '', 'pages': pages_param, 'templates': '1'})
    feed = urllib.urlopen(url, data)
    buf = feed.read()

    out = open(out_filename, 'w')
    out.write(buf)

    print 'Export saved %s' % out_filename


def export_at_once(page_names):
    """Perform a single export containing all pages."""

    print 'Getting export with full list of pages'
    pages_param = '\n'.join(page_names)
    get_export(pages_param, 'wiki_export.xml')


def export_page_at_time(page_names):
    """Perform an export for each page."""

    for idx, pages_param in enumerate(page_names):
        print 'Getting export for page %s' % pages_param
        get_export(pages_param, 'wiki_export%03d.xml' % idx)


def export(at_once=True):
    """Perform an export of a mediawiki wiki.

    First determine all the pages for all the namespaces.  Second
    request the export of the pages and save the returned xml export
    file.

    According to the doc at http://meta.wikimedia.org/wiki/Help:Export
    there is a max number of revisions that will be returned.  Hence
    it may be necessary to export each page separately.

    """

    namespaces = get_namespaces()

    page_names = []
    for ns in namespaces:
        page_names.extend(get_all_pages_for_namespace(ns))

    print 'Full list of pages:'
    pprint(page_names)

    if at_once:
        export_at_once(page_names)
    else:
        export_page_at_time(page_names)


def main():
    """Migrate a mediawiki wiki."""

    export()


if __name__ == '__main__':
    main()
