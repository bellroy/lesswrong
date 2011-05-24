
from pylons import g
from r2.lib.pages import *
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, urlopen
from urlparse import urlsplit,urlunsplit
from lxml.html import soupparser
from lxml.etree import tostring

log = g.log

def missing_content():
    return "<h2>Unable to fetch wiki page.  Try again later</h2>"

def cache_time():
    return int(g.wiki_page_cache_time)

def base_url(url):
    u = urlsplit(url)
    return urlunsplit([u[0],u[1]]+['','',''])

def fetch(url):
    log.debug('fetching: %s' % url)
    req = Request(url)
    content = urlopen(req).read()
    return content

def getParsedContent(str):
    parsed = soupparser.fromstring(str)
    try:
        elem=parsed.get_element_by_id('content')
        elem.set('id','wiki-content')
        return elem
    except KeyError:
        return parsed

class WikiPageCached:
    @staticmethod
    def html(page):
        url=page['url']
        content = g.rendercache.get(url)

        if not content:
            try:
                str = fetch(url)
                elem = getParsedContent(str)
                elem.make_links_absolute(base_url(url))
                content = tostring(elem, method='html', encoding='utf8', with_tail=False)
                g.rendercache.set(url, content, cache_time())
            except Exception as e:
                log.warn("Unable to fetch wiki page: '%s' %s"%(url,e))
                content = missing_content()
        return content

    @staticmethod
    def invalidate(page):
        g.rendercache.delete(page['url'])
        log.debug('invalidated: %s' % page['url'])

    
