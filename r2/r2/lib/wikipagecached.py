from pylons import g
from r2.lib.db.thing import Thing
from r2.lib.pages import *
from r2.lib.filters import remove_control_chars
from r2.models.printable import Printable
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, quote, urlopen
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
        elem = parsed.get_element_by_id(elementid)
    except KeyError:
        return parsed
    else:
        elem.attrib.pop('id')
        elem.set('class','wiki-content')
        return elem

class WikiPageCached:
    needed_cache_keys = ('content', 'title', 'etag')

    def __init__(self, config):
        self.config = config
        self._page = None
        self._error = False

    @classmethod
    def get_url_for_user_page(cls, user):
        page = 'User:' + quote(user.name)
        return 'http://wiki.lesswrong.com/wiki/' + page

    def getPage(self):
        url = self.config['url']
        hit = g.rendercache.get(url)
        if hit and isinstance(hit, dict) and all(k in hit for k in self.needed_cache_keys):
            # The above isinstance check guards against an old format of cache items
            return hit

        try:
            txt = fetch(url)
            elem = getParsedContent(txt, self.config.get('id', 'content'))
            elem.make_links_absolute(base_url(url))
            headlines = elem.cssselect('h1 .mw-headline')
            if headlines and len(headlines)>0:
                title = headlines[0].text_content()
            else:
                title = ''

            content_type = self.config.get('content-type', 'text/html')
            etag = '"%s"' % datetime.utcnow().isoformat()
            if content_type == 'text/html':
                content = tostring(elem, method='html', encoding='utf8', with_tail=False)
            else:
                # text_content() returns an _ElementStringResult, which derives from str
                # but scgi_base.py in flup contains the following broken assertion:
                # assert type(data) is str, 'write() argument must be string'
                # it should be assert isinstance(data, str)
                # So we have to force the _ElementStringResult to be a str
                content = str(elem.text_content())
            ret = {'content': content, 'title': title, 'etag': etag}
        except Exception as e:
            log.warn("Unable to fetch wiki page: '%s' %s"%(url,e))
            self._error = True
            ret = {'content': missing_content(), 'title': '', 'etag': ''}

        g.rendercache.set(url, ret, cache_time())
        return ret

    @property
    def page(self):
        if self._page is None:
            self._page = self.getPage()
        return self._page

    @property
    def success(self):
        _ = self.page
        return not self._error

    def content(self):
        return self.page['content']

    def etag(self):
        return self.page['etag']

    def title(self):
        return self.page['title']

    def invalidate(self):
        g.rendercache.delete(self.config['url'])
        log.debug('invalidated: %s' % self.config['url'])


class WikiPageThing(Thing, Printable):
    """
    Wiki pages are not Things. But sometimes we pretend they are, to make
    rendering more straightforward.
    """

    _nodb = True
    # These values have no real effect, but the attributes need to exist
    # in order for this class to successfully masquerade as a Thing.
    _type_name = 'wikipagething'
    _type_id = 0xdeadc0de
    _id = 0xbaddf00d

    def __init__(self, config):
        Thing.__init__(self)
        Printable.__init__(self)
        self.config = config
        self.wikipage = WikiPageCached(config)

    @staticmethod
    def cache_key(wrapped):
        return False

    @property
    def html(self):
        return self.wikipage.page['content']

    @property
    def success(self):
        return self.wikipage.success
