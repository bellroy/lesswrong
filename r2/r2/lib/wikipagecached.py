
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

def invalidate_link(page):
    return "<a id='invalidate' href='/invalidate_cache/%s'>Invalidate</a>"%page.name()

def fetch(url):
    log.debug('fetching: %s' % url)
    req = Request(url)
    content = urlopen(req).read()
    return content

def getParsedContent(str):
    parsed = soupparser.fromstring(str)
    try:
        return parsed.get_element_by_id('content')
    except KeyError:
        return parsed

# Modify the 'elem' by embedding an 'invalidate' link at the appropriate place
def embedInvalidateLink(page,elem):
    # Embed the invalidate cache link
    try:
        linkAsElem = soupparser.fromstring( invalidate_link(page) ).get_element_by_id('invalidate')
        elem.cssselect('.printfooter')[0].append(linkAsElem)
    except Exception as e:
        log.warning("Unable to embed invalidate link : %s"%e)

class WikiPageCached:
    @staticmethod
    def html(page):
        url=page.url()
        content = g.rendercache.get(url)

        if not content:
            try:
                str = fetch(url)
                elem = getParsedContent(str)
                elem.make_links_absolute(base_url(url))
                embedInvalidateLink(page,elem)
                content = tostring(elem, method='html', encoding='utf8', with_tail=False)
                g.rendercache.set(url, content, cache_time())
            except Exception as e:
                log.warn("Unable to fetch wiki page: '%s' %s"%(url,e))
                content = missing_content()
        return content

    @staticmethod
    def invalidate(page):
        g.rendercache.delete(page.url())
        log.debug('invalidated: %s' % page.url())

    
