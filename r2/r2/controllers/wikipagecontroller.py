from validator import *
from reddit_base import RedditController
from r2.lib.pages import *
from wiki_pages_embed import allWikiPagesCached

# Controller for pages pulled from wiki
class WikipageController(RedditController):

    # Get a full page with the wiki page embedded
    @validate(skiplayout=VBoolean('skiplayout'))
    def GET_wikipage(self,name,skiplayout):
        p = allWikiPagesCached[name]
        if skiplayout:
            # Get just the html of the wiki page
            html = WikiPageCached(p).html()
            return WikiPageInline(html=html, name=name, skiplayout=skiplayout).render()
        else:
            return WikiPage(name,p,skiplayout=skiplayout).render()

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
