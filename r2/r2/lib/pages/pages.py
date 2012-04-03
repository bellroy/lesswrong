# -*- coding: utf-8 -*-
# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is Reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
#
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################
from r2.lib.wrapped import Wrapped, NoTemplateFound
from r2.models import *
from r2.config import cache
from r2.lib.jsonresponse import json_respond
from r2.lib.jsontemplates import is_api
from pylons.i18n import _
from pylons import c, request, g
from pylons.controllers.util import abort

from r2.lib.captcha import get_iden
from r2.lib.filters import spaceCompress, _force_unicode, _force_utf8
from r2.lib.db.queries import db_sort
from r2.lib.menus import NavButton, NamedButton, NavMenu, JsButton, ExpandableButton, AbsButton
from r2.lib.menus import SubredditButton, SubredditMenu, menu
from r2.lib.strings import plurals, rand_strings, strings
from r2.lib.utils import title_to_url, query_string, UrlParser
from r2.lib.template_helpers import add_sr, get_domain
from r2.lib.promote import promote_builder_wrapper
from r2.lib.wikipagecached import WikiPageCached

import sys

datefmt = _force_utf8(_('%d %b %Y'))

def get_captcha():
    if not c.user_is_loggedin or c.user.needs_captcha():
        return get_iden()

class Reddit(Wrapped):
    '''Base class for rendering a page on reddit.  Handles toolbar creation,
    content of the footers, and content of the corner buttons.

    Constructor arguments:

        space_compress -- run r2.lib.filters.spaceCompress on render
        loginbox -- enable/disable rendering of the small login box in the right margin
          (only if no user is logged in; login box will be disabled for a logged in user)
        show_sidebar -- enable/disable content in the right margin

        infotext -- text to display in a <p class="infotext"> above the content
        nav_menus -- list of Menu objects to be shown in the area below the header
        content -- renderable object to fill the main content well in the page.

    settings determined at class-declaration time

        create_reddit_box  -- enable/disable display of the "Creat a reddit" box
        submit_box         -- enable/disable display of the "Submit" box
        searcbox           -- enable/disable display of the "search" box in the header
        extension_handling -- enable/disable rendering using non-html templates
          (e.g. js, xml for rss, etc.)
    '''

    create_reddit_box  = False
    submit_box         = False
    searchbox          = True
    extension_handling = True

    def __init__(self, space_compress = True, nav_menus = None, loginbox = True,
                 infotext = '', content = None, title = '', robots = None,
                 show_sidebar = True, body_class = None, top_filter = None, header_sub_nav = [], **context):
        Wrapped.__init__(self, **context)
        self.title          = title
        self.robots         = robots
        self.infotext       = infotext
        self.loginbox       = True
        self.show_sidebar   = show_sidebar
        self.space_compress = space_compress
        self.body_class     = body_class
        self.top_filter     = top_filter
        self.header_sub_nav = header_sub_nav

        #put the sort menus at the top
        self.nav_menu = MenuArea(menus = nav_menus) if nav_menus else None

        #add the infobar
        self.infobar = None
        if c.firsttime and c.site.firsttext and not infotext:
            infotext = c.site.firsttext
        if not infotext and hasattr(c.site, 'infotext'):
            infotext = c.site.infotext
        if infotext:
            self.infobar = InfoBar(message = infotext)

        self.srtopbar = None
        if not c.cname:
            self.srtopbar = SubredditTopBar()

        self._content = content
        self.toolbars = self.build_toolbars()

    def rightbox(self):
        """generates content in <div class="rightbox">"""

        ps = PaneStack(css_class='spacer')

        if self.searchbox:
            ps.append(GoogleSearchForm())

        if not c.user_is_loggedin and self.loginbox:
            ps.append(LoginFormWide())
        else:
            ps.append(ProfileBar(c.user, self.corner_buttons()))

        filters_ps = PaneStack(div=True)
        for toolbar in self.toolbars:
            filters_ps.append(toolbar)

        if self.nav_menu:
            filters_ps.append(self.nav_menu)

        if not filters_ps.empty:
            ps.append(SideBox(filters_ps))

        #don't show the subreddit info bar on cnames
        if c.user_is_admin and not isinstance(c.site, FakeSubreddit) and not c.cname:
            ps.append(SubredditInfoBar())

        if self.extension_handling:
            ps.append(FeedLinkBar())

        ps.append(SideBoxPlaceholder('side-meetups', _('Nearest Meetups'), '/meetups', sr_path=False))
        ps.append(SideBoxPlaceholder('side-comments', _('Recent Comments'), '/comments'))
        ps.append(SideBoxPlaceholder('side-posts', _('Recent Posts'), '/recentposts'))

        if g.recent_edits_feed:
            ps.append(RecentWikiEditsBox(g.recent_edits_feed))

        for feed_url in g.feedbox_urls:
            ps.append(FeedBox(feed_url))

        ps.append(SideBoxPlaceholder('side-tags', _('Tags')))
        ps.append(SideBoxPlaceholder('side-monthly-contributors', _('Top Contributors, 30 Days')))
        ps.append(SideBoxPlaceholder('side-contributors', _('Top Contributors, All Time')))

        if g.site_meter_codename:
            ps.append(SiteMeter(g.site_meter_codename))

        return ps

    def render(self, *a, **kw):
        """Overrides default Wrapped.render with two additions
           * support for rendering API requests with proper wrapping
           * support for space compression of the result
        In adition, unlike Wrapped.render, the result is in the form of a pylons
        Response object with it's content set.
        """
        try:
            res = Wrapped.render(self, *a, **kw)
            if is_api():
                res = json_respond(res)
            elif self.space_compress:
                res = spaceCompress(res)
            c.response.content = res
        except NoTemplateFound, e:
            # re-raise the error -- development environment
            if g.debug:
                s = sys.exc_info()
                raise s[1], None, s[2]
            # die gracefully -- production environment
            else:
                abort(404, "not found")
        return c.response

    def corner_buttons(self):
        """set up for buttons in upper right corner of main page."""
        buttons = []
        if c.user_is_loggedin:
            if c.user.name in g.admins:
                if c.user_is_admin:
                   buttons += [NamedButton("adminoff", False,
                                           nocname=not c.authorized_cname,
                                           target = "_self")]
                else:
                   buttons += [NamedButton("adminon",  False,
                                           nocname=not c.authorized_cname,
                                           target = "_self")]

            buttons += [NamedButton('submit', sr_path = not c.default_sr,
                                    nocname=not c.authorized_cname)]
            if c.user.safe_karma >= g.discussion_karma_to_post:
                buttons += [NamedButton('meetups/new', False,
                                        nocname=not c.authorized_cname)]
            buttons += [NamedButton("prefs", False,
                                  css_class = "pref-lang")]
            buttons += [NamedButton("logout", False,
                                    nocname=not c.authorized_cname,
                                    target = "_self")]

        return NavMenu(buttons, base_path = "/", type = "buttons")

    def footer_nav(self):
        """navigation buttons in the footer."""
        buttons = [NamedButton("help", False, nocname=True),
                   NamedButton("blog", False, nocname=True),
                   NamedButton("stats", False, nocname=True),
                   NamedButton("feedback",     False),
                   NamedButton("bookmarklets", False),
                   NamedButton("socialite",    False),
                   NamedButton("buttons",      True),
                   NamedButton("widget",       True),
                   NamedButton("code",         False, nocname=True),
                   NamedButton("mobile",       False, nocname=True),
                   NamedButton("store",        False, nocname=True),
                   NamedButton("ad_inq",       False, nocname=True),
                   ]

        return NavMenu(buttons, base_path = "/", type = "flatlist")

    def header_nav(self):
        """Navigation menu for the header"""

        menu_stack = PaneStack()

        # Ensure the default button is the first tab
        #default_button_name = c.site.default_listing

        main_buttons = [
            ExpandableButton('main', dest = '/promoted', sr_path = False, sub_menus =
                             [ NamedButton('posts', dest = '/promoted', sr_path = False),
                               NamedButton('comments', dest = '/comments', sr_path = False)]),
            ExpandableButton('discussion', dest = "/r/discussion/new", sub_reddit = "/r/discussion/", sub_menus =
                             [ NamedButton('posts', dest = "/r/discussion/new", sr_path = False),
                               NamedButton('comments', dest = "/r/discussion/comments", sr_path = False)])
       ]

        menu_stack.append(NavMenu(main_buttons, title = _('Filter by'), _id='nav', type='navlist'))


        if self.header_sub_nav:
            menu_stack.append(NavMenu(self.header_sub_nav, title = _('Filter by'), _id='filternav', type='navlist'))

        return menu_stack

    def right_menu(self):
        """docstring for right_menu"""
        buttons = [
          AbsButton('wiki', 'http://wiki.lesswrong.com'),
          NamedButton('sequences', sr_path=False),
          NamedButton('about', sr_path=False)
        ]

        return NavMenu(buttons, title = _('Filter by'), _id='rightnav', type='navlist')

    def build_toolbars(self):
        """Additional toolbars/menus"""
        return []

    def __repr__(self):
        return "<Reddit>"

    @staticmethod
    def content_stack(*a):
        """Helper method for reordering the content stack."""
        return PaneStack(filter(None, a))

    def content(self):
        """returns a Wrapped (or renderable) item for the main content div."""
        return self.content_stack(self.infobar, self._content)

class LoginFormWide(Wrapped):
    """generates a login form suitable for the 300px rightbox."""
    pass

class SideBoxPlaceholder(Wrapped):
    """A minimal side box with a heading and an anchor.

    If javascript is off the anchor may be followed and if it is on
    then javascript will replace the content of the div with the HTML
    result of an ajax request.
    """

    def __init__(self, node_id, link_text, link_path=None, sr_path=True):
        Wrapped.__init__(self, node_id=node_id, link_text=link_text, link_path=link_path, sr_path=sr_path)

class SpaceCompressedWrapped(Wrapped):
    """Overrides default Wrapped.render to do space compression as well."""
    def render(self, *a, **kw):
        res = Wrapped.render(self, *a, **kw)
        res = spaceCompress(res)
        return res

class RecentItems(SpaceCompressedWrapped):
    def __init__(self, *args, **kwargs):
        self.things = self.init_builder()
        Wrapped.__init__(self, *args, **kwargs)

    def query(self):
        raise NotImplementedError

    def init_builder(self):
        return QueryBuilder(self.query(), wrap=self.wrap_thing)

    @staticmethod
    def wrap_thing(thing):
        w = Wrapped(thing)

        if isinstance(thing, Link):
            w.render_class = InlineArticle
        elif isinstance(thing, Comment):
            w.render_class = InlineComment

        return w

class RecentComments(RecentItems):
    def query(self):
        return c.current_or_default_sr.get_comments('new', 'all')

    def init_builder(self):
        return UnbannedCommentBuilder(
            self.query(),
            num = 5,
            wrap = RecentItems.wrap_thing,
            skip = True,
            sr_ids = [c.current_or_default_sr._id]
        )

class RecentArticles(RecentItems):
    def query(self):
        q = c.current_or_default_sr.get_links('new', 'all')
        q._limit = 10
        return q

class RecentArticlesPage(Wrapped):
    """Compact recent article listing page"""
    def __init__(self, content, *a, **kw):
        Wrapped.__init__(self, content=content, *a, **kw)

class RecentPromotedArticles(RecentItems):
    def query(self):
        sr = DefaultSR()
        q = sr.get_links('blessed', 'all')
        q._limit = 4
        return q

class TopContributors(SpaceCompressedWrapped):
    def __init__(self, *args, **kwargs):
        from r2.lib.user_stats import top_users
        uids = top_users()
        users = Account._byID(uids, data=True, return_dict=False)

        # Filter out accounts banned from the default subreddit
        sr = Subreddit._by_name(g.default_sr)
        self.things = filter(lambda user: not sr.is_banned(user), users)

        Wrapped.__init__(self, *args, **kwargs)

class TopMonthlyContributors(SpaceCompressedWrapped):
    def __init__(self, *args, **kwargs):
        from r2.lib.user_stats import cached_all_user_change
        uids_karma = cached_all_user_change()[1]
        uids = map(lambda x: x[0], uids_karma)
        users = Account._byID(uids, data=True, return_dict=False)

        # Add the monthly karma to the account objects
        karma_lookup = dict(uids_karma)
        for u in users:
            u.monthly_karma = karma_lookup[u._id]

        # Filter out accounts banned from the default subreddit
        sr = Subreddit._by_name(g.default_sr)
        self.things = filter(lambda user: not sr.is_banned(user), users)

        Wrapped.__init__(self, *args, **kwargs)

class TagCloud(SpaceCompressedWrapped):

    numbers = ('one','two','three','four','five','six','seven','eight','nine','ten')

    def nav(self):
        cloud = Tag.tag_cloud_for_subreddits([c.current_or_default_sr._id])

        buttons = []
        for tag, weight in cloud:
            buttons.append(NavButton(tag.name, tag.name, css_class=self.numbers[weight - 1]))

        return NavMenu(buttons, type="flatlist", separator=' ', base_path='/tag/')

class SubredditInfoBar(Wrapped):
    """When not on Default, renders a sidebox which gives info about
    the current reddit, including links to the moderator and
    contributor pages, as well as links to the banning page if the
    current user is a moderator."""
    def nav(self):
        is_moderator = c.user_is_loggedin and \
            c.site.is_moderator(c.user) or c.user_is_admin

        buttons = [NavButton(plurals.moderators, 'moderators')]
        if c.site.type != 'public':
            buttons.append(NavButton(plurals.contributors, 'contributors'))

        if is_moderator:
            buttons.append(NamedButton('edit'))
            buttons.extend([NavButton(menu.banusers, 'banned'),
                            NamedButton('spam')])
        return [NavMenu(buttons, type = "flatlist", base_path = "/about/")]

class SideBox(Wrapped):
    """Generic sidebox"""
    def __init__(self, content, _id = None, css_class = ''):
        Wrapped.__init__(self, content=content, _id = _id, css_class = css_class)


class PrefsPage(Reddit):
    """container for pages accessible via /prefs.  No extension handling."""

    extension_handling = False

    def __init__(self, show_sidebar = True, *a, **kw):
        Reddit.__init__(self, show_sidebar = show_sidebar,
                        title = "%s - %s" % (_("Preferences"), c.site.title),
                        *a, **kw)

    def header_nav(self):
        buttons = [NavButton(menu.options, ''),
                   NamedButton('friends'),
                   NamedButton('update'),
                   NamedButton('delete')]
        return NavMenu(buttons, base_path = "/prefs", _id='nav', type='navlist')

class PrefOptions(Wrapped):
    """Preference form for updating language and display options"""
    def __init__(self, done = False):
        Wrapped.__init__(self, done = done)

class PrefUpdate(Wrapped):
    """Preference form for updating email address and passwords"""
    pass

class PrefDelete(Wrapped):
    """preference form for deleting a user's own account."""
    pass


class MessagePage(Reddit):
    """Defines the content for /message/*"""
    def __init__(self, *a, **kw):
        if not kw.has_key('show_sidebar'):
            kw['show_sidebar'] = True
        Reddit.__init__(self, *a, **kw)
        self.replybox = CommentReplyBox()

    def content(self):
        return self.content_stack(self.replybox, self.infobar, self._content)

    def header_nav(self):
        buttons =  [NamedButton('compose'),
                    NamedButton('inbox'),
                    NamedButton('sent')]
        return NavMenu(buttons, base_path = "/message", _id='nav', type='navlist')

class MessageCompose(Wrapped):
    """Compose message form."""
    def __init__(self,to='', subject='', message='', success='',
                 captcha = None):
        Wrapped.__init__(self, to = to, subject = subject,
                         message = message, success = success,
                         captcha = captcha)


class BoringPage(Reddit):
    """parent class For rendering all sorts of uninteresting,
    sortless, navless form-centric pages.  The top navmenu is
    populated only with the text provided with pagename and the page
    title is 'reddit.com: pagename'"""

    extension_handling= False

    def __init__(self, pagename, **context):
        self.pagename = pagename
        Reddit.__init__(self, title = "%s - %s" % (_force_unicode(pagename), c.site.title),
                        **context)

class FormPage(BoringPage):
    """intended for rendering forms with no rightbox needed or wanted"""
    def __init__(self, pagename, show_sidebar = False, *a, **kw):
        BoringPage.__init__(self, pagename,  show_sidebar = show_sidebar,
                            *a, **kw)


class LoginPage(BoringPage):
    """a boring page which provides the Login/register form"""
    def __init__(self, **context):
        context['loginbox'] = False
        self.dest = context.get('dest', '')
        context['show_sidebar'] = False
        BoringPage.__init__(self,  _("Login or register"), **context)

    def content(self):
        kw = {}
        for x in ('user_login', 'user_reg'):
            kw[x] = getattr(self, x) if hasattr(self, x) else ''
        return Login(dest = self.dest, **kw)

class Login(Wrapped):
    """The two-unit login and register form."""
    def __init__(self, user_reg = '', user_login = '', dest=''):
        Wrapped.__init__(self, user_reg = user_reg, user_login = user_login,
                         dest = dest)


class SearchPage(BoringPage):
    """Search results page"""
    searchbox = False

    def __init__(self, pagename, prev_search, elapsed_time, num_results, *a, **kw):
        self.searchbar = SearchBar(prev_search = prev_search,
                                   elapsed_time = elapsed_time,
                                   num_results = num_results)
        BoringPage.__init__(self, pagename, robots='noindex', *a, **kw)

    def content(self):
        return self.content_stack(self.searchbar, self.infobar, self._content)

class LinkInfoPage(Reddit):
    """Renders the varied /info pages for a link.  The Link object is
    passed via the link argument and the content passed to this class
    will be rendered after a one-element listing consisting of that
    link object.

    In addition, the rendering is reordered so that any nav_menus
    passed to this class will also be rendered underneath the rendered
    Link.
    """

    create_reddit_box  = False
    robots             = None

    @staticmethod
    def comment_permalink_wrapper(comment, link):
        wrapped = Wrapped(link, link_title=comment.make_permalink_title(link), for_comment_permalink=True)
        wrapped.render_class = CommentPermalink
        return wrapped

    def __init__(self, link = None, comment = None,
                 link_title = '', is_canonical = False, *a, **kw):

        link.render_full = True

        # TODO: temp hack until we find place for builder_wrapper
        from r2.controllers.listingcontroller import ListingController
        if comment:
            link_wrapper = lambda link: self.comment_permalink_wrapper(comment, link)
        else:
            link_wrapper = ListingController.builder_wrapper
        link_builder = IDBuilder(link._fullname,
                                 wrap = link_wrapper)

        # link_listing will be the one-element listing at the top
        self.link_listing = LinkListing(link_builder, nextprev=False).listing()

        # link is a wrapped Link object
        self.link = self.link_listing.things[0]

        link_title = ((self.link.title) if hasattr(self.link, 'title') else '')
        if comment:
            title = comment.make_permalink_title(link)

            # Comment permalinks should not be indexed, there's too many of them
            self.robots = 'noindex'

            if is_canonical == False:
                self.canonical_link = comment.make_permalink(link)
        else:
            params = {'title':_force_unicode(link_title), 'site' : c.site.title}
            title = strings.link_info_title % params

            if not (c.default_sr and is_canonical):
                # Not on the main page, so include a pointer to the canonical URL for this link
                self.canonical_link = link.canonical_url

        Reddit.__init__(self, title = title, body_class = 'post', robots = self.robots, *a, **kw)

    def content(self):
        return self.content_stack(self.infobar, self.link_listing, self._content)

    def build_toolbars(self):
        return []

class LinkInfoBar(Wrapped):
    """Right box for providing info about a link."""
    def __init__(self, a = None):
        if a:
            a = Wrapped(a)

        Wrapped.__init__(self, a = a, datefmt = datefmt)


class EditReddit(Reddit):
    """Container for the about page for a reddit"""
    extension_handling= False

    def __init__(self, *a, **kw):
        is_moderator = c.user_is_loggedin and \
            c.site.is_moderator(c.user) or c.user_is_admin

        title = _('Manage your category') if is_moderator else \
                _('About %(site)s') % dict(site=c.site.name)

        Reddit.__init__(self, title = title, *a, **kw)

class SubredditsPage(Reddit):
    """container for rendering a list of reddits."""
    submit_box   = False
    def __init__(self, prev_search = '', num_results = 0, elapsed_time = 0,
                 title = '', loginbox = True, infotext = None, *a, **kw):
        Reddit.__init__(self, title = title, loginbox = loginbox, infotext = infotext,
                        *a, **kw)
        self.sr_infobar = InfoBar(message = strings.sr_subscribe)

    def header_nav(self):
        buttons =  [NavButton(menu.popular, ""),
                    NamedButton("new")]
        if c.user_is_admin:
            buttons.append(NamedButton("banned"))

        return NavMenu(buttons, base_path = '/categories')

    def content(self):
        return self.content_stack(self.sr_infobar, self._content)

    def rightbox(self):
        ps = Reddit.rightbox(self)
        position = 1 if not c.user_is_loggedin else 0
        ps.insert(position, SubscriptionBox())
        return ps

class MySubredditsPage(SubredditsPage):
    """Same functionality as SubredditsPage, without the search box."""

    def content(self):
        return self.content_stack(self.infobar, self._content)


def votes_visible(user):
    """Determines whether to show/hide a user's votes.  They are visible:
     * if the current user is the user in question
     * if the user has a preference showing votes
     * if the current user is an administrator
    """
    return ((c.user_is_loggedin and c.user.name == user.name) or
            user.pref_public_votes or
            c.user_is_admin)

class ProfilePage(Reddit):
    """Container for a user's profile page.  As such, the Account
    object of the user must be passed in as the first argument, along
    with the current sub-page (to determine the title to be rendered
    on the page)"""

    searchbox         = False
    create_reddit_box = False
    submit_box        = False
    

    def __init__(self, user, *a, **kw):
        self.user     = user
        Reddit.__init__(self, body_class = "profile_page", *a, **kw)

    def header_nav(self):
        path = "/user/%s/" % self.user.name
        main_buttons = [NavButton(menu.overview, '/', aliases = ['/overview']),
                   NavButton(_('Comments'), 'comments'),
                   NamedButton('submitted')]

        if votes_visible(self.user):
            main_buttons += [NamedButton('liked'),
                        NamedButton('disliked'),
                        NamedButton('hidden')]

        if c.user_is_loggedin and self.user._id == c.user._id:
            # User is looking at their own page
            main_buttons.append(NamedButton('drafts'))

        return NavMenu(main_buttons, base_path = path, title = _('View'), _id='nav', type='navlist')


    def rightbox(self):
        rb = Reddit.rightbox(self)
        if self.user != c.user:
            rb.push(ProfileBar(self.user))
        return rb

class ProfileBar(Wrapped):
    """Draws a right box for info about the user (karma, etc)"""
    def __init__(self, user, buttons = None):
        Wrapped.__init__(self, user = user, buttons = buttons)
        self.isFriend = self.user._id in c.user.friends \
            if c.user_is_loggedin else False
        self.isMe = (self.user == c.user)

class MenuArea(Wrapped):
    """Draws the gray box at the top of a page for sort menus"""
    def __init__(self, menus = []):
        Wrapped.__init__(self, menus = menus)

class InfoBar(Wrapped):
    """Draws the yellow box at the top of a page for info"""
    def __init__(self, message = ''):
        Wrapped.__init__(self, message = message)

class UnfoundPage(Wrapped):
    """Wrapper for the 404 page"""
    def __init__(self, choice='a'):
        Wrapped.__init__(self, choice=choice)

class ErrorPage(Wrapped):
    """Wrapper for an error message"""
    def __init__(self, message = _("You aren't allowed to do that.")):
        Wrapped.__init__(self, message = message)

class Profiling(Wrapped):
    """Debugging template for code profiling using built in python
    library (only used in middleware)"""
    def __init__(self, header = '', table = [], caller = [], callee = [], path = ''):
        Wrapped.__init__(self, header = header, table = table, caller = caller,
                         callee = callee, path = path)

class Over18(Wrapped):
    """The creepy 'over 18' check page for nsfw content."""
    pass

class SubredditTopBar(Wrapped):
    """The horizontal strip at the top of most pages for navigating
    user-created reddits."""
    def __init__(self):
        Wrapped.__init__(self)

        my_reddits = []
        sr_ids = Subreddit.user_subreddits(c.user if c.user_is_loggedin else None)
        if sr_ids:
            my_reddits = Subreddit._byID(sr_ids, True,
                                         return_dict = False)
            my_reddits.sort(key = lambda sr: sr.name.lower())

        drop_down_buttons = []
        for sr in my_reddits:
            drop_down_buttons.append(SubredditButton(sr))

        #leaving the 'home' option out for now
        #drop_down_buttons.insert(0, NamedButton('home', sr_path = False,
        #                                        css_class = 'top-option',
        #                                        dest = '/'))
        drop_down_buttons.append(NamedButton('edit', sr_path = False,
                                             css_class = 'bottom-option',
                                             dest = '/categories/'))
        self.sr_dropdown = SubredditMenu(drop_down_buttons,
                                         title = _('My categories'),
                                         type = 'srdrop')


        pop_reddits = Subreddit.default_srs(c.content_langs, limit = 30)
        buttons = []
        for sr in c.recent_reddits:
            # Extra guarding for Issue #50
            if hasattr(sr, 'name'):
                buttons.append(SubredditButton(sr))

        for sr in pop_reddits:
            if sr not in c.recent_reddits:
                buttons.append(SubredditButton(sr))

        self.sr_bar = NavMenu(buttons, type='flatlist', separator = '-',
                                        _id = 'sr-bar')

class SubredditBox(Wrapped):
    """A content pane that has the lists of subreddits that go in the
    right pane by default"""
    def __init__(self):
        Wrapped.__init__(self)

        self.title = _('Other reddit communities')
        self.subtitle = 'Visit your subscribed categories (in bold) or explore new ones'
        self.create_link = ('/categories/', menu.more)
        self.more_link   = ('/categories/create', _('Create'))

        my_reddits = []
        sr_ids = Subreddit.user_subreddits(c.user if c.user_is_loggedin else None)
        if sr_ids:
            my_reddits = Subreddit._byID(sr_ids, True,
                                         return_dict = False)
            my_reddits.sort(key = lambda sr: sr._downs, reverse = True)

        display_reddits = my_reddits[:g.num_side_reddits]

        #remove the current reddit
        display_reddits = filter(lambda x: x != c.site, display_reddits)

        pop_reddits = Subreddit.default_srs(c.content_langs, limit = g.num_side_reddits)
        #add english reddits to the list
        if c.content_langs != 'all' and 'en' not in c.content_langs:
            en_reddits = Subreddit.default_srs(['en'])
            pop_reddits += [sr for sr in en_reddits if sr not in pop_reddits]

        for sr in pop_reddits:
            if len(display_reddits) >= g.num_side_reddits:
                break

            if sr != c.site and sr not in display_reddits:
                display_reddits.append(sr)

        col1, col2 = [], []
        cur_col, other = col1, col2
        for sr in display_reddits:
            cur_col.append((sr, sr in my_reddits))
            cur_col, other = other, cur_col

        self.cols = ((col1, col2))
        self.mine = my_reddits

class SubscriptionBox(Wrapped):
    """The list of reddits a user is currently subscribed to to go in
    the right pane."""
    def __init__(self):
        sr_ids = Subreddit.user_subreddits(c.user if c.user_is_loggedin else None)
        srs = Subreddit._byID(sr_ids, True, return_dict = False)
        srs.sort(key = lambda sr: sr.name.lower())
        b = IDBuilder([sr._fullname for sr in srs])
        self.reddits = LinkListing(b).listing().things

class CreateSubreddit(Wrapped):
    """reddit creation form."""
    def __init__(self, site = None, name = '', listings = []):
        Wrapped.__init__(self, site = site, name = name, listings = listings)

class SubredditStylesheet(Wrapped):
    """form for editing or creating subreddit stylesheets"""
    def __init__(self, site = None,
                 stylesheet_contents = ''):
        Wrapped.__init__(self, site = site,
                         stylesheet_contents = stylesheet_contents)

class CssError(Wrapped):
    """Rendered error returned to the stylesheet editing page via ajax"""
    def __init__(self, error):
        # error is an instance of cssutils.py:ValidationError
        Wrapped.__init__(self, error = error)

class UploadedImage(Wrapped):
    "The page rendered in the iframe during an upload of a header image"
    def __init__(self,status,img_src, name="", errors = {}):
        self.errors = list(errors.iteritems())
        Wrapped.__init__(self, status=status, img_src=img_src, name = name)

class ImageBrowser(Wrapped):
    "The page rendered in the tinyMCE image browser window"
    def __init__(self, article):
        self.article = article
        Wrapped.__init__(self)

class Password(Wrapped):
    """Form encountered when 'recover password' is clicked in the LoginFormWide."""
    def __init__(self, success=False):
        Wrapped.__init__(self, success = success)

class PasswordReset(Wrapped):
    """Template for generating an email to the user who wishes to
    reset their password (step 2 of password recovery, after they have
    entered their user name in Password.)"""
    pass

class ResetPassword(Wrapped):
    """Form for actually resetting a lost password, after the user has
    clicked on the link provided to them in the Password_Reset email
    (step 3 of password recovery.)"""
    pass


class Captcha(Wrapped):
    """Container for rendering robot detection device."""
    def __init__(self, error=None, tabular=True, label=True):
        self.error = _('Try entering those letters again') if error else ""
        self.iden = get_captcha()
        Wrapped.__init__(self, tabular=tabular, label=label)

class CommentReplyBox(Wrapped):
    """Used on LinkInfoPage to render the comment reply form at the
    top of the comment listing as well as the template for the forms
    which are JS inserted when clicking on 'reply' in either a comment
    or message listing."""
    def __init__(self, link_name='', captcha=None, action = 'comment'):
        Wrapped.__init__(self, link_name = link_name, captcha = captcha,
                         action = action)

class CommentListing(Wrapped):
    """Comment heading and sort, limit options"""
    def __init__(self, content, num_comments, nav_menus = []):
        Wrapped.__init__(self, content=content, num_comments=num_comments, menus = nav_menus)

class PermalinkMessage(Wrapped):
    """renders the box on comment pages that state 'you are viewing a
    single comment's thread'"""
    def __init__(self, comments_url, has_more_comments=False):
        self.comments_url = comments_url
        self.has_more_comments = has_more_comments
        Wrapped.__init__(self)


class PaneStack(Wrapped):
    """Utility class for storing and rendering a list of block elements."""

    def __init__(self, panes=[], div_id = None, css_class=None, div=False):
        div = div or div_id or css_class or False
        self.div_id    = div_id
        self.css_class = css_class
        self.div       = div
        self.stack     = list(panes)
        Wrapped.__init__(self)

    def append(self, item):
        """Appends an element to the end of the current stack"""
        self.stack.append(item)

    def push(self, item):
        """Prepends an element to the top of the current stack"""
        self.stack.insert(0, item)

    def insert(self, *a):
        """inerface to list.insert on the current stack"""
        return self.stack.insert(*a)

    @property
    def empty(self):
        """Return True if the stack has any items, False otherwise"""
        return len(self.stack) == 0

class SearchForm(Wrapped):
    """The simple search form in the header of the page.  prev_search
    is the previous search."""
    def __init__(self, prev_search = ''):
        Wrapped.__init__(self, prev_search = prev_search)

class GoogleSearchForm(Wrapped):
    """Shows Google Custom Search box"""
    def __init__(self):
        Wrapped.__init__(self)

class WikiPageList(Wrapped):
    """Shows Wiki Page List box"""
    def __init__(self, link):
        if link:
          self.articleurl = link.url
        else:
          self.articleurl = None
        Wrapped.__init__(self)

class GoogleSearchResultsFrame(Wrapped):
    """Shows Google Custom Search box"""
    def __init__(self):
        Wrapped.__init__(self)

class GoogleSearchResults(BoringPage):
    """Receieves search results from Google"""

    def __init__(self, pagename, *a, **kw):
        kw['content'] = GoogleSearchResultsFrame()
        BoringPage.__init__(self, pagename, robots='noindex', *a, **kw)

    def content(self):
      return self.content_stack(self._content)
        # return self.content_stack(self.infobar,
                                  # self.nav_menu, self._content)

class ArticleNavigation(Wrapped):
  """Generates article navigation fragment for the supplied link"""
  def __init__(self, link, author):
    Wrapped.__init__(self, article=link, author=author)

class SearchBar(Wrapped):
    """More detailed search box for /search and /categories pages.
    Displays the previous search as well as info of the elapsed_time
    and num_results if any."""
    def __init__(self, num_results = 0, prev_search = '', elapsed_time = 0, **kw):

        # not listed explicitly in args to ensure it translates properly
        self.header = kw.get('header', _("Previous search"))

        self.prev_search  = prev_search
        self.elapsed_time = elapsed_time

        # All results are approximate unless there are fewer than 10.
        if num_results > 10:
            self.num_results = (num_results / 10) * 10
        else:
            self.num_results = num_results

        Wrapped.__init__(self)


class Frame(Wrapped):
    """Frameset for the FrameToolbar used when a user hits /goto and
    has pref_toolbar set.  The top 30px of the page are dedicated to
    the toolbar, while the rest of the page will show the results of
    following the link."""
    def __init__(self, url='', title='', fullname=''):
        Wrapped.__init__(self, url = url, title = title, fullname = fullname)

class FrameToolbar(Wrapped):
    """The reddit voting toolbar used together with Frame."""
    extension_handling = False
    def __init__(self, link = None, **kw):
        self.title = link.title
        Wrapped.__init__(self, link = link, *kw)



class NewLink(Wrapped):
    """Render the link submission form"""
    def __init__(self, captcha = None, article = '', title= '', subreddits = (), tags = (), sr_id = None):
        Wrapped.__init__(self, captcha = captcha, article = article,
                         title = title, subreddits = subreddits, tags = tags,
                         sr_id = sr_id)

class EditLink(Wrapped):
    """Render the edit link form"""
    pass

class ShareLink(Wrapped):
    def __init__(self, link_name = "", emails = None):
        captcha = Captcha() if c.user.needs_captcha() else None
        Wrapped.__init__(self, link_name = link_name,
                         emails = c.user.recent_share_emails(),
                         captcha = captcha)

class Share(Wrapped):
    pass

class Mail_Opt(Wrapped):
    pass

class OptOut(Wrapped):
    pass

class OptIn(Wrapped):
    pass


# class UserStats(Wrapped):
#     """For drawing the stats page, which is fetched from the cache."""
#     def __init__(self):
#         Wrapped.__init__(self)
#         cache_stats = cache.get('stats')
#         if cache_stats:
#             top_users, top_day, top_week = cache_stats

#             #lookup user objs
#             uids = []
#             uids.extend(u    for u in top_users)
#             uids.extend(u[0] for u in top_day)
#             uids.extend(u[0] for u in top_week)
#             users = Account._byID(uids, data = True)

#             self.top_users = (users[u]            for u in top_users)
#             self.top_day   = ((users[u[0]], u[1]) for u in top_day)
#             self.top_week  = ((users[u[0]], u[1]) for u in top_week)
#         else:
#             self.top_users = self.top_day = self.top_week = ()


class ButtonEmbed(Wrapped):
    """Generates the JS wrapper around the buttons for embedding."""
    def __init__(self, button = None, width = 100, height=100, referer = "", url = ""):
        Wrapped.__init__(self, button = button, width = width, height = height,
                         referer=referer, url = url)

class ButtonLite(Wrapped):
    """Generates the JS wrapper around the buttons for embedding."""
    def __init__(self, image = None, link = None, url = "", styled = True, target = '_top'):
        Wrapped.__init__(self, image = image, link = link, url = url, styled = styled, target = target)

class Button(Wrapped):
    """the voting buttons, embedded with the ButtonEmbed wrapper, shown on /buttons"""
    extension_handling = False
    def __init__(self, link = None, button = None, css=None,
                 url = None, title = '', score_fmt = None, vote = True, target = "_parent",
                 bgcolor = None, width = 100):
        Wrapped.__init__(self, link = link, score_fmt = score_fmt,
                         likes = link.likes if link else None,
                         button = button, css = css, url = url, title = title,
                         vote = vote, target = target, bgcolor=bgcolor, width=width)

class ButtonNoBody(Button):
    """A button page that just returns the raw button for direct embeding"""
    pass

class ButtonDemoPanel(Wrapped):
    """The page for showing the different styles of embedable voting buttons"""
    pass


class Feedback(Wrapped):
    """The feedback and ad inquery form(s)"""
    def __init__(self, captcha=None, title=None, action='/feedback',
                    message='', name='', email='', replyto='', success = False):
        Wrapped.__init__(self, captcha = captcha, title = title, action = action,
                         message = message, name = name, email = email, replyto = replyto,
                         success = success)


class WidgetDemoPanel(Wrapped):
    """Demo page for the .embed widget."""
    pass

class Socialite(Wrapped):
    """Demo page for the socialite Firefox extension"""
    pass

class Bookmarklets(Wrapped):
    """The bookmarklets page."""
    def __init__(self, buttons=["reddit", "like", "dislike",
                             "save", "serendipity!"]):
        Wrapped.__init__(self, buttons = buttons)



class AdminTranslations(Wrapped):
    """The translator control interface, used for determining which
    user is allowed to edit which translation file and for providing a
    summary of what translation files are done and/or in use."""
    def __init__(self):
        from r2.lib.translation import list_translations
        Wrapped.__init__(self)
        self.translations = list_translations()


class Embed(Wrapped):
    """wrapper for embedding /help into reddit as if it were not on a separate wiki."""
    def __init__(self,content = ''):
        Wrapped.__init__(self, content = content)


class Page_down(Wrapped):
    def __init__(self, **kw):
        message = kw.get('message', _("This feature is currently unavailable. Sorry"))
        Wrapped.__init__(self, message = message)

# Classes for dealing with friend/moderator/contributor/banned lists

# TODO: if there is time, we could roll these Ajaxed classes into the
# JsonTemplates framework...
class Ajaxed():
    """Base class for allowing simple interaction of UserTableItem and
    UserItem classes to be edited via JS and AJax requests.  In
    analogy with Wrapped, this class provides an interface for
    'rendering' dictionary representations of the data which can be
    passed to the client via JSON over AJAX"""
    __slots__ = ['kind', 'action', 'data']

    def __init__(self, kind, action):
        self._ajax = dict(kind=kind,
                          action = None,
                          data = {})

    def for_ajax(self, action = None):
        self._ajax['action'] = action
        self._ajax['data'] = self.ajax_render()
        return self._ajax

    def ajax_render(self, style="html"):
        return {}


class UserTableItem(Wrapped, Ajaxed):
    """A single row in a UserList of type 'type' and of name
    'container_name' for a given user.  The provided list of 'cells'
    will determine what order the different columns are rendered in.
    Currently, this list can consist of 'user', 'sendmessage' and
    'remove'."""
    def __init__(self, user, type, cellnames, container_name, editable):
        self.user, self.type, self.cells = user, type, cellnames
        self.container_name = container_name
        self.name           = "tr_%s_%s" % (user.name, type)
        self.editable       = editable
        Wrapped.__init__(self)
        Ajaxed.__init__(self, 'UserTable', 'add')

    def ajax_render(self, style="html"):
        """Generates a 'rendering' of this item suitable for
        processing by JS for insert or removal from an existing
        UserList"""
        cells = []
        for cell in self.cells:
            r = Wrapped.part_render(self, 'cell_type', cell)
            cells.append(spaceCompress(r))
        return dict(cells=cells, id=self.type, name=self.name)

    def __repr__(self):
        return '<UserTableItem "%s">' % self.user.name

class UserList(Wrapped):
    """base class for generating a list of users"""
    form_title     = ''
    table_title    = ''
    type           = ''
    container_name = ''
    cells          = ('user', 'sendmessage', 'remove')
    _class         = ""

    def __init__(self, editable = True):
        self.editable = editable
        Wrapped.__init__(self)

    def ajax_user(self, user):
        """Convenience method for constructing a UserTableItem
        instance of the user with type, container_name, etc. of this
        UserList instance"""
        return UserTableItem(user, self.type, self.cells, self.container_name,
                             self.editable)

    @property
    def users(self, site = None):
        """Generates a UserTableItem wrapped list of the Account
        objects which should be present in this UserList."""
        uids = self.user_ids()
        if uids:
            users = Account._byID(uids, True, return_dict = False)
            return [self.ajax_user(u) for u in users]
        else:
            return ()

    def user_ids(self):
        """virtual method for fetching the list of ids of the Accounts
        to be listing in this UserList instance"""
        raise NotImplementedError

    @property
    def container_name(self):
        return c.site._fullname

class FriendList(UserList):
    """Friend list on /pref/friends"""
    type = 'friend'

    @property
    def form_title(self):
        return _('Add a friend')

    @property
    def table_title(self):
        return _('Your friends')

    def user_ids(self):
        return c.user.friends

    @property
    def container_name(self):
        return c.user._fullname

class ContributorList(UserList):
    """Contributor list on a restricted/private reddit."""
    type = 'contributor'

    @property
    def form_title(self):
        return _('Add contributor')

    @property
    def table_title(self):
        return _("Contributors to %(reddit)s") % dict(reddit = c.site.name)

    def user_ids(self):
        return c.site.contributors

class ModList(UserList):
    """Moderator list for a reddit."""
    type = 'moderator'

    @property
    def form_title(self):
        return _('Add moderator')

    @property
    def table_title(self):
        return _("Moderators to %(reddit)s") % dict(reddit = c.site.name)

    def user_ids(self):
        return c.site.moderators

class EditorList(UserList):
    """Editor list for a reddit."""
    type = 'editor'

    @property
    def form_title(self):
        return _('Add editor')

    @property
    def table_title(self):
        return _("Editors of %(reddit)s") % dict(reddit = c.site.name)

    def user_ids(self):
        return c.site.editors

class BannedList(UserList):
    """List of users banned from a given reddit"""
    type = 'banned'

    @property
    def form_title(self):
        return _('Ban users')

    @property
    def table_title(self):
        return  _('Banned users')

    def user_ids(self):
        return c.site.banned


class DetailsPage(LinkInfoPage):
    extension_handling= False

    def content(self):
        # TODO: a better way?
        from admin_pages import Details
        return self.content_stack(self.link_listing, Details(link = self.link))

class Cnameframe(Wrapped):
    """The frame page."""
    def __init__(self, original_path, subreddit, sub_domain):
        Wrapped.__init__(self, original_path=original_path)
        if sub_domain and subreddit and original_path:
            self.title = "%s - %s" % (subreddit.title, sub_domain)
            u = UrlParser(subreddit.path + original_path)
            u.hostname = get_domain(cname = False, subreddit = False)
            u.update_query(**request.get.copy())
            u.put_in_frame()
            self.frame_target = u.unparse()
        else:
            self.title = ""
            self.frame_target = None

class PromotePage(Reddit):
    create_reddit_box  = False
    submit_box         = False
    extension_handling = False

    def __init__(self, title, nav_menus = None, *a, **kw):
        buttons = [NamedButton('current_promos', dest = ''),
                   NamedButton('new_promo')]

        menu  = NavMenu(buttons, title='show', base_path = '/promote',
                        type='flatlist')

        if nav_menus:
            nav_menus.insert(0, menu)
        else:
            nav_menus = [menu]

        Reddit.__init__(self, title, nav_menus = nav_menus, *a, **kw)


class PromotedLinks(Wrapped):
    def __init__(self, current_list, *a, **kw):
        self.things = current_list

        Wrapped.__init__(self, datefmt = datefmt, *a, **kw)

class PromoteLinkForm(Wrapped):
    def __init__(self, sr = None, link = None, listing = '',
                 timedeltatext = '', *a, **kw):
        Wrapped.__init__(self, sr = sr, link = link,
                         datefmt = datefmt,
                         timedeltatext = timedeltatext,
                         listing = listing,
                         *a, **kw)

class FeedLinkBar(Wrapped): pass

class AboutBox(Wrapped): pass

class FeedBox(Wrapped):
    def __init__(self, feed_url, *a, **kw):
        self.feed_url = feed_url
        Wrapped.__init__(self, *a, **kw)

class RecentWikiEditsBox(Wrapped):
    def __init__(self, feed_url, *a, **kw):
        self.feed_url = feed_url
        Wrapped.__init__(self, *a, **kw)

class SiteMeter(Wrapped):
    def __init__(self, codename, *a, **kw):
        self.codename = codename
        Wrapped.__init__(self, *a, **kw)

class UpcomingMeetups(SpaceCompressedWrapped):
    def __init__(self, location, max_distance, *a, **kw):
        meetups = Meetup.upcoming_meetups_near(location, max_distance, 2)
        Wrapped.__init__(self, meetups=meetups, location=location, *a, **kw)

class MeetupsMap(Wrapped):
    def __init__(self, location, max_distance, *a, **kw):
        meetups = Meetup.upcoming_meetups_near(location, max_distance)
        Wrapped.__init__(self, meetups=meetups, location=location, *a, **kw)

class NotEnoughKarmaToPost(Wrapped):
	  pass

class ShowMeetup(Wrapped):
    """docstring for ShowMeetup"""
    def __init__(self, meetup, **kw):
        # title_params = {'title':_force_unicode(meetup.title), 'site' : c.site.title}
        # title = strings.show_meetup_title % title_params
        Wrapped.__init__(self, meetup = meetup, **kw)

class NewMeetup(Wrapped):
    def __init__(self, *a, **kw):
        Wrapped.__init__(self, *a, **kw)

class EditMeetup(Wrapped):
    pass

class MeetupIndexPage(Reddit):
  def __init__(self, **context):
    self.meetups = context.get("content", None)
    Reddit.__init__(self, **context)

  def content(self):
    return MeetupIndex(self.meetups)

class MeetupIndex(Wrapped):
  def __init__(self, meetups = [], *a, **kw):
    self.meetups = meetups
    Wrapped.__init__(self, *a, **kw)

  def meetups(self):
    return self.meetups

class WikiPageInline(Wrapped): pass

class WikiPage(Reddit):
    def __init__(self, name, page, skiplayout, **context):
        wikiPage = WikiPageCached(page)
        html = wikiPage.html()
        self.pagename = wikiPage.title()
        Reddit.__init__(self,
                        content = WikiPageInline(html=html, name=name,
                                                 skiplayout=skiplayout,title=self.pagename),
                        title = self.pagename,
                        space_compress=False,
                        **context)

