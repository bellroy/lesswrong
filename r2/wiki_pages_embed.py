from pylons.i18n import _
from pylons import c


class AboutPage:
    @staticmethod
    def route(): return "/about-less-wrong"
    @staticmethod
    def url(): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Aboutpage'
    @staticmethod
    def title(): return _('About - '+c.site.name)
    @staticmethod
    def name(): return 'about'

class MainPage:
    @staticmethod
    def route(): return "/"
    @staticmethod
    def url(): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Homepage'
    @staticmethod
    def title(): return _(c.site.name)
    @staticmethod
    def name(): return 'main'

class CommentPage:
    @staticmethod
    def url(): return 'http://wiki.lesswrong.com/wiki/Lesswrong:Commentmarkuphelp'
    @staticmethod
    def name(): return 'comment-help'

allWikiPagesCached = [AboutPage(), MainPage(), CommentPage()]

