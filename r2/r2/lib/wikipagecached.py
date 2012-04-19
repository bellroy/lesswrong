
from pylons import g
from r2.lib.pages import *
from r2.lib.filters import remove_control_chars
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, urlopen
from urlparse import urlsplit,urlunsplit
from lxml.html import soupparser
from lxml.etree import tostring
from datetime import datetime

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

def getParsedContent(str, elementid):
    parsed = soupparser.fromstring(remove_control_chars(str))
    try:
        elem=parsed.get_element_by_id(elementid)
        elem.set('id','wiki-content')
        return elem
    except KeyError:
        return parsed

class WikiPageCached:
    def __init__(self, config):
        self.config = config
        self._page = None

    def getPage(self):
        url=self.config['url']
        content_type = self.config.get('content-type', 'text/html')
        hit = g.rendercache.get(url)
        content, title, etag = hit if hit else (None,None,None)

        if not content:
            try:
                txt = fetch(url)
                elem = getParsedContent(txt, self.config.get('id', 'content'))
                elem.make_links_absolute(base_url(url))
                headlines = elem.cssselect('h1 .mw-headline')
                if headlines and len(headlines)>0:
                    title = headlines[0].text_content()

                etag = '"%s"' % datetime.utcnow().isoformat()
                if content_type == 'text/css':
                    # text_content() returns an _ElementStringResult, which derives from str
                    # but scgi_base.py in flup contains the following broken assertion:
                    # assert type(data) is str, 'write() argument must be string'
                    # it should be assert isinstance(data, str)
                    # So we have to force the _ElementStringResult to be a str
                    content = str(elem.text_content())
                else:
                    content = tostring(elem, method='html', encoding='utf8', with_tail=False)
                g.rendercache.set(url, (content,title,etag), cache_time())
            except Exception as e:
                log.warn("Unable to fetch wiki page: '%s' %s"%(url,e))
                content = missing_content()

        return {
          'title': title,
          'content': content,
          'etag': etag,
        }

    @property
    def page(self):
        if self._page is None:
            self._page = self.getPage()
        return self._page

    def content(self):
        return self.page['content']

    def etag(self):
        return self.page['etag']

    def title(self):
        return self.page['title']

    def invalidate(self):
        g.rendercache.delete(self.config['url'])
        log.debug('invalidated: %s' % self.config['url'])


