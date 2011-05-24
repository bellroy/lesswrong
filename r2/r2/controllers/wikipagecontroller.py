from reddit_base import RedditController
from r2.lib.pages import *
from wiki_pages_embed import allWikiPagesCached

# Controller for pages pulled from wiki
class WikipageController(RedditController):

    def GET_wikipage(self,name):
        p = allWikiPagesCached[name]
        return WikiPage(name,p).render()

    def GET_html(self,name):
        p = allWikiPagesCached[name]
        return WikiPageCached().html(p)

    def POST_invalidate_cache(self, name):
        p = allWikiPagesCached[name]
        WikiPageCached.invalidate(p)
        return self.redirect(p['route'])
