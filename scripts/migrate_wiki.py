#!/usr/bin/env python

import os
import datetime
import optparse
import urllib
import urllib2
import multipartposthandler
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
    feed = urllib2.urlopen(url, data)
    buf = feed.read()

    out = open(out_filename, 'w')
    out.write(buf)

    print 'Export saved %s' % out_filename


def export_at_once(export_dir, page_names):
    """Perform a single export containing all pages."""

    print 'Getting export with full list of pages'
    pages_param = '\n'.join(page_names)
    export_filename = os.path.join(export_dir, 'wiki_export.xml')
    get_export(pages_param, export_filename)

    return [export_filename]


def export_page_at_time(export_dir, page_names):
    """Perform an export for each page."""

    export_filenames = []
    for idx, pages_param in enumerate(page_names):
        print 'Getting export for page %s' % pages_param
        export_filename = os.path.join(export_dir, 'wiki_export%04d.xml' % idx)
        get_export(pages_param, export_filename)
        export_filenames.append(export_filename)

    return export_filenames


def export_wiki(export_dir, at_once):
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
        export_filenames = export_at_once(export_dir, page_names)
    else:
        export_filenames = export_page_at_time(export_dir, page_names)

    return export_filenames


def setup_opener():
    """Build a url opener that can handle cookies and multipart form data."""

    print 'Building url opener'
    cookie_handler = urllib2.HTTPCookieProcessor()
    multipart_handler = multipartposthandler.MultipartPostHandler()
    opener = urllib2.build_opener(cookie_handler, multipart_handler)
    urllib2.install_opener(opener)


def login(password):
    """Login to the destination wiki as the Admin user.

    This will setup our cookies so that we can do the import as the
    admin user.

    """

    print 'Logging in as the Admin user'
    url = 'http://shank.trike.com.au/mediawiki/index.php?title=Special:UserLogin&action=submitlogin&type=login'
    data = urllib.urlencode({'wpLoginattempt': 'Log in', 'wpName': 'Admin', 'wpPassword': password})
    feed = urllib2.urlopen(url, data)
    buf = feed.read()
    tree = etree.fromstring(buf, parser)
    nodes = tree.xpath('//a[@title="Log out"]')
    if not nodes:
        raise Exception('Failed to login to destination wiki')


def get_edit_token():
    """Return the edit token that is needed to do an import."""

    print 'Getting edit token'
    url = 'http://shank.trike.com.au/mediawiki/index.php?title=Special:Import'
    feed = urllib2.urlopen(url)
    buf = feed.read()
    tree = etree.fromstring(buf, parser)
    nodes = tree.xpath('//input[@name="editToken"]')
    if not nodes or 'value' not in nodes[0].attrib:
        raise Exception('Failed to get edit token needed for importing')
    token = nodes[0].get('value')
    return token


def do_import(export_filename, token):
    """Send the POST import request with the file to be imported."""

    print 'Importing %s' % export_filename
    url = 'http://shank.trike.com.au/mediawiki/index.php?title=Special:Import&action=submit'
    export_file = open(export_filename, 'rb')
    data = {'source': 'upload', 'log-comment': 'migrate_wiki.py script', 'xmlimport': export_file, 'editToken': token }
    feed = urllib2.urlopen(url, data)
    buf = feed.read()
    tree = etree.fromstring(buf, parser)
    nodes = tree.xpath('//div[@id="bodyContent"]/p[2]')
    if not nodes or not nodes[0].text.startswith('Import finished!'):
        raise Exception('Failed to upload file, perhaps export file exceeds max size, try without the --at-once option')


def import_wiki(export_filenames, password):
    """Import the specified export files into the destination wiki."""

    setup_opener()

    login(password)

    token = get_edit_token()

    for export_filename in export_filenames:
        do_import(export_filename, token)


def main():
    """Migrate a mediawiki wiki."""

    opt_parser = optparse.OptionParser()
    opt_parser.add_option('-p', '--password',
                          dest='password',
                          help='destination wiki admin password (REQUIRED)')
    opt_parser.add_option('-a', '--at-once',
                          action='store_true', default=False,
                          help='get single export file in one go, otherwise get export file for each wiki page')
    options, args = opt_parser.parse_args()

    if options.password:
        export_dir = os.path.join(os.getcwd(), 'wiki_export_%s' % datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        os.makedirs(export_dir)

        export_filenames = export_wiki(export_dir, options.at_once)
        import_wiki(export_filenames, options.password)
    else:
        opt_parser.print_help()


if __name__ == '__main__':
    main()
