
from pylons import g
from r2.lib.pages import *
from r2.lib.filters import remove_control_chars
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
    log.debug('fetched %d bytes' % len(content))
    return content

def getParsedContent(str):
    parsed = soupparser.fromstring(remove_control_chars(str))
    try:
        elem=parsed.get_element_by_id('content')
        elem.set('id','wiki-content')
        return elem
    except KeyError:
        return parsed

class WikiPageCached:
    def __init__(self, page):
        self.page = page
        self.loaded = False

    def getPage(self):
        url=self.page['url']
        contentTitle = g.rendercache.get(url)
        [content,title] = contentTitle if contentTitle else [None,None]

        if not content:
            try:
                str = fetch(url)
                elem = getParsedContent(str)
                elem.make_links_absolute(base_url(url))
                headlines = elem.cssselect('h1 .mw-headline')
                if headlines and len(headlines)>0:
                    title = headlines[0].text_content()
                content = tostring(elem, method='html', encoding='utf8', with_tail=False)
                g.rendercache.set(url, [content,title], cache_time())
            except Exception as e:
                log.warn("Unable to fetch wiki page: '%s' %s"%(url,e))
                content = missing_content()

        self.titleStr = title
        self.content = content
        self.loaded = True

    def html(self):
        if not self.loaded:
            self.getPage()
        return self.content

    def title(self):
        if not self.loaded:
            self.getPage()
        return self.titleStr

    def invalidate(self):
        g.rendercache.delete(self.page['url'])
        log.debug('invalidated: %s' % self.page['url'])

    
