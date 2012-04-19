from validator import *
from reddit_base import RedditController
from r2.lib.pages import *
from wiki_pages_embed import allWikiPagesCached
from pylons import response
from pylons.controllers.util import etag_cache

# Controller for pages pulled from wiki
class WikipageController(RedditController):

    # Get a full page with the wiki page embedded
    @validate(skiplayout=VBoolean('skiplayout'))
    def GET_wikipage(self,name,skiplayout):
        p = allWikiPagesCached[name]
        content_type = p.get('content-type', 'text/html')
        if content_type == 'text/html':
          if skiplayout:
              # Get just the html of the wiki page
              html = WikiPageCached(p).content()
              return WikiPageInline(html=html, name=name, skiplayout=skiplayout).render()
          else:
              return WikiPage(name,p,skiplayout=skiplayout).render()
        else:
          # Send the content back as is, with cache control
          page = WikiPageCached(p)
          response.headers['Content-Type'] = content_type
          response.headers['Cache-Control'] = 'max-age=%d' % 300
          etag_cache(page.etag())
          return page.content()

    @validate(VUser(),
              skiplayout=VBoolean('skiplayout'))
    def POST_invalidate_cache(self, name, skiplayout):
        p = allWikiPagesCached[name]
        WikiPageCached(p).invalidate()
        if p.has_key('route'):
            if skiplayout:
                return self.redirect('/wiki/'+p['route']+'?skiplayout=on')
            else:
                return self.redirect('/wiki/'+p['route'])
        else:
            return "Done"
