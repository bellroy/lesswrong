
from pylons import g
from r2.lib.pages import *
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, urlopen
from lxml.html import soupparser
from lxml.etree import tostring

log = g.log

class WikiPageCached:
    def title(self):
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def fetch(self):
        u = self.url()
        content = g.rendercache.get(u)
        if not content:
            log.debug('fetching: %s' % u)
            req = Request(u)
            content = urlopen(req).read()
            g.rendercache.set(u, content)
        return content

    def invalidate(self):
        u = self.url()
        g.rendercache.delete(u)
        log.debug('invalidated: %s' % u)

    def getContent(self,str):
        return soupparser.fromstring(str).get_element_by_id('content')

    def invalidate_link(self):
        return "<a id='invalidate' href='/invalidate_cache/%s'>Invalidate</a>"%self.name()

    def html(self):
        str = self.fetch()
        elem = self.getContent(str)

        # Embed the invalidate cache link
        linkAsElem = soupparser.fromstring( self.invalidate_link() ).get_element_by_id('invalidate')
        elem.cssselect('.printfooter')[0].append(linkAsElem)
        return tostring(elem, method='html', encoding='utf8', with_tail=False)

class AboutPage(WikiPageCached):
    def url(self): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Aboutpage'
    def title(self): return _('About - Less wrong')
    def name(self): return 'about'

class MainPage(WikiPageCached):
    def url(self): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Homepage'
    def title(self): return _('Less wrong')
    def name(self): return 'main'

class CommentPage(WikiPageCached):
    def url(self): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Commentmarkuphelp'
    def name(self): return 'comment-help'

allWikiPagesCached = [AboutPage(), MainPage(), CommentPage()]
