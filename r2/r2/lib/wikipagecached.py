
from pylons import g
from r2.lib.pages import *
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, urlopen
from lxml.html import soupparser
from lxml.etree import tostring

log = g.log

class WikiPageCached:
    @staticmethod
    def missing_content():
        return "<h2>Unable to fetch wiki page.  Try again later</h2>"

    def title(self):
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def fetch(self):
        u = self.url()
        content = g.rendercache.get(u)
        try:
            if not content:
                log.debug('fetching: %s' % u)
                req = Request(u)
                content = urlopen(req).read()
                g.rendercache.set(u, content)
        except IOError as e:
            log.warn("Unable to fetch wiki page: '%s' %s"%(u,e))
            content = WikiPageCached.missing_content()
        return content

    def invalidate(self):
        u = self.url()
        g.rendercache.delete(u)
        log.debug('invalidated: %s' % u)

    def getParsedContent(self,str):
        parsed = soupparser.fromstring(str)
        try:
            return parsed.get_element_by_id('content')
        except KeyError:
            return parsed

    def invalidate_link(self):
        return "<a id='invalidate' href='/invalidate_cache/%s'>Invalidate</a>"%self.name()

    def html(self):
        str = self.fetch()
        elem = self.getParsedContent(str)

        # Embed the invalidate cache link
        try:
            linkAsElem = soupparser.fromstring( self.invalidate_link() ).get_element_by_id('invalidate')
            elem.cssselect('.printfooter')[0].append(linkAsElem)
        except:
            pass
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
