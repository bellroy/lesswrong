from reddit_base import RedditController
from r2.lib.pages import *
from wiki_pages_embed import allWikiPagesCached
from mako.template import Template

# Controller for pages pulled from wiki
class WikipageController(RedditController):

    # Get a full page with the wiki page embedded
    def GET_wikipage(self,name):
        p = allWikiPagesCached[name]
        return WikiPage(name,p).render()

    # Get just the html of the wiki page
    def GET_html(self,name):
        p = allWikiPagesCached[name]
        html = WikiPageCached().html(p)
        form = Template(filename='r2/templates/invalidate_wikipagecache.html').get_def("invalidate_link").render(name=name)
        return html+form

    def POST_invalidate_cache(self, name):
        p = allWikiPagesCached[name]
        WikiPageCached.invalidate(p)
        if p.has_key('route'):
            return self.redirect(p['route'])
        elif p.has_key('htmlroute'):
            return self.redirect('/wiki'+p['htmlroute'])
        else:
            return "Done"
