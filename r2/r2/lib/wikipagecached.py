
from pylons import g
from r2.lib.pages import *
from pylons.i18n import _, ungettext
from urllib2 import Request, HTTPError, URLError, urlopen
from urlparse import urlsplit,urlunsplit
from lxml.html import soupparser
from lxml.etree import tostring

log = g.log

class WikiPageCached:
    @staticmethod
    def missing_content():
        return "<h2>Unable to fetch wiki page.  Try again later</h2>"

    @staticmethod
    def cache_time():
        return int(g.wiki_page_cache_time)

    def title(self):
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def base_url(self):
        u = urlsplit(self.url())
        return urlunsplit([u[0],u[1]]+['','',''])

    def invalidate_link(self):
        return "<a id='invalidate' href='/invalidate_cache/%s'>Invalidate</a>"%self.name()

    def fetch(self):
        u = self.url()
        log.debug('fetching: %s' % u)
        req = Request(u)
        content = urlopen(req).read()
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

    def embedInvalidateLink(self, elem):
        # Embed the invalidate cache link
        try:
            linkAsElem = soupparser.fromstring( self.invalidate_link() ).get_element_by_id('invalidate')
            elem.cssselect('.printfooter')[0].append(linkAsElem)
        except:
            pass

    def html(self):
        u=self.url()
        content = g.rendercache.get(u)

        if not content:
            try:
                str = self.fetch()
                elem = self.getParsedContent(str)
                self.embedInvalidateLink(elem)
                elem.make_links_absolute(self.base_url())
                content = tostring(elem, method='html', encoding='utf8', with_tail=False)
                g.rendercache.set(u, content, WikiPageCached.cache_time())
            except Exception as e:
                log.warn("Unable to fetch wiki page: '%s' %s"%(u,e))
                content = WikiPageCached.missing_content()
        return content


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
