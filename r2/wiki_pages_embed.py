# Configuration file for wiki pages to be embedded (and cached) on the main site.
# Pages are configured using a python hash.  
# - The hash key is a name used as a parameter to refer to the page in question
# url : is the page to be embedded
# title : the page title and heading.  Not required if the page is not to be accessible
#         as a toplevel page
# route : The route to access the page at.  May be ommited
# htmlroute : If present, the *html only* of the page will be accessible at /wiki/{htmlroute}
#             Useful for getting wiki content via an ajax request


from pylons.i18n import _
from pylons import c

allWikiPagesCached = \
  {
    'about': { 'url' : 'http://wiki.lesswrong.com/wiki/Lesswrong:Aboutpage',
               'title' : lambda: _('About - '+c.site.title),
               'route' : 'Aboutpage'
               },

    'main': { 'url' : 'http://wiki.lesswrong.com/wiki/Lesswrong:Homepage',
              'title' : lambda: _(c.site.title),
              'route' : 'Homepage'
              },

    'comment-help' : { 'url' : 'http://wiki.lesswrong.com/wiki/Lesswrong:Commentmarkuphelp',
                       'route' : 'Commentmarkuphelp'
                       }
    }

