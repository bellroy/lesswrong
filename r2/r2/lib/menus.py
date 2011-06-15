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
from wrapped import Wrapped
from pylons import c, request, g
from utils import  query_string, timeago
from strings import StringHandler, plurals
from r2.lib.db import operators
from r2.lib.filters import _force_unicode
from pylons.i18n import _
#from r2.config import cache


class MenuHandler(StringHandler):
    """Bastard child of StringHandler and plurals.  Menus are
    typically a single word (and in some cases, a single plural word
    like 'moderators' or 'contributors' so this class first checks its
    own dictionary of string translations before falling back on the
    plurals list."""
    def __getattr__(self, attr):
        try:
            return StringHandler.__getattr__(self, attr)
        except KeyError:
            return getattr(plurals, attr)

# selected menu styles, primarily used on the main nav bar
menu_selected=StringHandler(hot          = _("Popular"),
                            new          = _("What's new"),
                            top          = _("Top scoring"),
                            controversial= _("Most controversial"),
                            saved        = _("Saved"),
                            recommended  = _("Recommended"),
                            promote      = _('Promote'),
                            )

# translation strings for every menu on the site
menu =   MenuHandler(hot          = _('Popular'),
                     new          = _('New'),
                     old          = _('Old'),
                     ups          = _('Ups'),
                     downs        = _('Downs'),
                     top          = _('Top'),
                     more         = _('More'),
                     relevance    = _('Relevance'),
                     controversial  = _('Controversial'),
                     saved        = _('Saved'),
                     recommended  = _('Recommended'),
                     rising       = _('Rising'),
                     admin        = _('Admin'),
                     drafts       = _('Drafts'),
                     blessed      = _('Promoted'),
                     comments     = _('Comments'),
                     posts        = _('Posts'),
                     topcomments     = _('Top Comments'),
                     newcomments     = _('New Comments'),

                     # time sort words
                     hour         = _('This hour'),
                     day          = _('Today'),
                     week         = _('This week'),
                     month        = _('This month'),
                     year         = _('This year'),
                     all          = _('All time'),

                     # "kind" words
                     spam         = _("Spam"),
                     autobanned   = _("Autobanned"),

                     # reddit header strings
                     adminon      = _("Turn admin on"),
                     adminoff     = _("Turn admin off"),
                     prefs        = _("Preferences"),
                     stats        = _("Stats"),
                     submit       = _("Create new article"),
                     meetupsnew   = _("Add new meetup"),
                     help         = _("Help"),
                     blog         = _("Blog"),
                     logout       = _("Log out"),

                     #reddit footer strings
                     feedback     = _("Feedback"),
                     bookmarklets = _("Bookmarklets"),
                     socialite    = _("Socialite"),
                     buttons      = _("Buttons"),
                     widget       = _("Widget"),
                     code         = _("Code"),
                     mobile       = _("Mobile"),
                     store        = _("Store"),
                     ad_inq       = _("Advertise"),

                     #preferences
                     options      = _('Options'),
                     friends      = _("Friends"),
                     update       = _("Password/email"),
                     delete       = _("Delete"),

                     # messages
                     compose      = _("Compose"),
                     inbox        = _("Inbox"),
                     sent         = _("Sent"),

                     # comments
                     related      = _("Related"),
                     details      = _("Details"),

                     # reddits
                     main         = _("Main"),
                     discussion   = _("Discussion"),
                     wiki         = _("Wiki"),
                     sequences    = _("Sequences"),
                     about        = _("About"),
                     edit         = _("Edit"),
                     banned       = _("Banned"),
                     banusers     = _("Ban users"),

                     popular      = _("Popular"),
                     create       = _("Create"),
                     mine         = _("My reddits"),

                     i18n         = _("Translate site"),
                     promoted     = _("Promoted"),
                     reporters    = _("Reporters"),
                     reports      = _("Reports"),
                     reportedauth = _("Reported authors"),
                     info         = _("Info"),
                     share        = _("Share"),

                     overview     = _("Overview"),
                     submitted    = _("Submitted"),
                     liked        = _("Liked"),
                     disliked     = _("Disliked"),
                     hidden       = _("Hidden"),
                     deleted      = _("Deleted"),
                     reported     = _("Reported"),

                     promote      = _('Promote'),
                     new_promo    = _('New promoted link'),
                     current_promos = _('Promoted links'),
                     )

class Styled(Wrapped):
    """Rather than creating a separate template for every possible
    menu/button style we might want to use, this class overrides the
    render function to render only the <%def> in the template whose
    name matches 'style'.

    Additionally, when rendering, the '_id' and 'css_class' attributes
    are intended to be used in the outermost container's id and class
    tag.
    """
    def __init__(self, style, _id = '', css_class = '', **kw):
        self._id = _id
        self.css_class = css_class
        self.style = style
        Wrapped.__init__(self, **kw)

    def render(self, **kw):
        """Using the canonical template file, only renders the <%def>
        in the template whose name is given by self.style"""
        style = kw.get('style', c.render_style or 'html')
        return Wrapped.part_render(self, self.style, style = style, **kw)



def menu_style(type):
    """Simple manager function for the styled menus.  Returns a
    (style, css_class) pair given a 'type', defaulting to style =
    'dropdown' with no css_class."""
    default = ('select', '')
    d = dict(heavydrop = ('dropdown', 'heavydrop'),
             lightdrop = ('dropdown', 'lightdrop'),
             tabdrop = ('dropdown', 'tabdrop'),
             srdrop = ('dropdown', 'srdrop'),
             flatlist =  ('flatlist', ''),
             tabmenu = ('tabmenu', ''),
             buttons = ('userlinks', ''),
             select  = ('select', ''),
             navlist  = ('navlist', ''),
             dropdown2 = ('dropdown2', ''))
    return d.get(type, default)



class NavMenu(Styled):
    """generates a navigation menu.  The intention here is that the
    'style' parameter sets what template/layout to use to differentiate, say,
    a dropdown from a flatlist, while the optional _class, and _id attributes
    can be used to set individualized CSS."""

    def __init__(self, options, default = None, title = '', type = "dropdown",
                 base_path = '', separator = '|', **kw):
        self.options = options
        self.base_path = base_path
        kw['style'], kw['css_class'] = menu_style(type)

        #used by flatlist to delimit menu items
        self.separator = separator

        # since the menu contains the path info, it's buttons need a
        # configuration pass to get them pointing to the proper urls
        for opt in self.options:
            opt.build(self.base_path)

        # selected holds the currently selected button defined as the
        # one whose path most specifically matches the current URL
        # (possibly None)
        self.default = default
        self.selected = self.find_selected()
        self.enabled = True

        Styled.__init__(self, title = title, **kw)

    def find_selected(self):
        maybe_selected = [o for o in self.options if o.is_selected()]
        if maybe_selected:
            # pick the button with the most restrictive pathing
            maybe_selected.sort(lambda x, y:
                                len(y.bare_path) - len(x.bare_path))
            return maybe_selected[0]
        elif self.default:
            #lookup the menu with the 'dest' that matches 'default'
            for opt in self.options:
                if opt.dest == self.default:
                    return opt

    def __repr__(self):
        return "<NavMenu>"

    def __iter__(self):
        for opt in self.options:
            yield opt

class NavButton(Styled):
    """Smallest unit of site navigation.  A button once constructed
    must also have its build() method called with the current path to
    set self.path.  This step is done automatically if the button is
    passed to a NavMenu instance upon its construction."""
    def __init__(self, title, dest, sr_path = True,
                 nocname=False, opt = '', aliases = [],
                 target = "", style = "plain", **kw):

        # keep original dest to check against c.location when rendering
        self.aliases = set(a.rstrip('/') for a in aliases)
        self.aliases.add(dest.rstrip('/'))
        self.dest = dest

        Styled.__init__(self, style = style, sr_path = sr_path,
                        nocname = nocname, target = target,
                        title = title, opt = opt, **kw)

    def build(self, base_path = ''):
        '''Generates the href of the button based on the base_path provided.'''

        # append to the path or update the get params dependent on presence
        # of opt
        if self.opt:
            p = request.get.copy()
            p[self.opt] = self.dest
        else:
            p = {}
            base_path = ("%s/%s/" % (base_path, self.dest)).replace('//', '/')

        self.bare_path = _force_unicode(base_path.replace('//', '/')).lower()
        self.bare_path = self.bare_path.rstrip('/')

        # append the query string
        base_path += query_string(p)

        # since we've been sloppy of keeping track of "//", get rid
        # of any that may be present
        self.path = base_path.replace('//', '/')

    def is_selected(self):
        """Given the current request path, would the button be selected."""
        if hasattr(self, 'name') and self.name == 'home':
            return False
        if self.opt:
            return request.params.get(self.opt, '') in self.aliases
        else:
            stripped_path = request.path.rstrip('/').lower()
            ustripped_path = _force_unicode(stripped_path)
            if stripped_path == self.bare_path:
                return True
            if stripped_path in self.aliases:
                return True

    def selected_title(self):
        """returns the title of the button when selected (for cases
        when it is different from self.title)"""
        return self.title

class AbsButton(NavButton):
    """A button for linking to an absolute URL"""
    def __init__(self, title, dest):
        self.path = dest
        NavButton.__init__(self, title, dest, False)

    def build(self, base_path = ''):
        pass

    def is_selected(self):
        return False

class SubredditButton(NavButton):
    def __init__(self, sr):
        self.sr = sr
        NavButton.__init__(self, sr.name, sr.path, False)

    def build(self, base_path = ''):
        self.path = self.sr.path

    def is_selected(self):
        return c.site == self.sr


class NamedButton(NavButton):
    """Convenience class for handling the majority of NavButtons
    whereby the 'title' is just the translation of 'name' and the
    'dest' defaults to the 'name' as well (unless specified
    separately)."""

    def __init__(self, name, sr_path = True, nocname=False, dest = None, **kw):
        self.name = name.replace('/', '')
        NavButton.__init__(self, menu[self.name], name if dest is None else dest,
                           sr_path = sr_path, nocname=nocname, **kw)

    def selected_title(self):
        """Overrides selected_title to use menu_selected dictionary"""
        try:
            return menu_selected[self.name]
        except KeyError:
            return NavButton.selected_title(self)

class ExpandableButton(NamedButton):
    def __init__(self, name, sr_path = True, nocname=False, dest = None, 
                 sub_reddit = "/", sub_menus=[], **kw):
        self.sub = sub_menus
        self.sub_reddit  = sub_reddit
        NamedButton.__init__(self,name,sr_path,nocname,dest,**kw)

    def sub_menus(self):
        return self.sub

    def is_selected(self):
        return c.site.path == self.sub_reddit

class JsButton(NavButton):
    """A button which fires a JS event and thus has no path and cannot
    be in the 'selected' state"""
    def __init__(self, title, style = 'js', **kw):
        NavButton.__init__(self, title, '', style = style, **kw)

    def build(self, *a, **kw):
        self.path = 'javascript:void(0)'

    def is_selected(self):
        return False

class PageNameNav(Styled):
    """generates the links and/or labels which live in the header
    between the header image and the first nav menu (e.g., the
    subreddit name, the page name, etc.)"""
    pass

class SimpleGetMenu(NavMenu):
    """Parent class of menus used for sorting and time sensitivity of
    results.  More specifically, defines a type of menu which changes
    the url by adding a GET parameter with name 'get_param' and which
    defaults to 'default' (both of which are class-level parameters).

    The value of the GET parameter must be one of the entries in
    'cls.options'.  This parameter is also used to construct the list
    of NavButtons contained in this Menu instance.  The goal here is
    to have a menu object which 'out of the box' is self validating."""
    options   = []
    get_param = ''
    title     = ''
    default = None

    def __init__(self, type = 'select', **kw):
        kw['default'] = kw.get('default', self.default)
        kw['base_path'] = kw.get('base_path') or request.path
        buttons = [NavButton(self.make_title(n), n, opt = self.get_param)
                   for n in self.options]
        NavMenu.__init__(self, buttons, type = type, **kw)
        #if kw.get('default'):
        #    self.selected = kw['default']

    def make_title(self, attr):
        return menu[attr]

    @classmethod
    def operator(self, sort):
        """Converts the opt into a DB-esque operator used for sorting results"""
        return None

class SortMenu(SimpleGetMenu):
    """The default sort menu."""
    get_param = 'sort'
    default   = 'hot'
    options   = ('hot', 'new', 'top', 'old', 'controversial')

    def __init__(self, **kw):
        kw['title'] = _("Sort By") + ':'
        SimpleGetMenu.__init__(self, **kw)

    @classmethod
    def operator(self, sort):
        if sort == 'hot':
            return operators.desc('_hot')
        elif sort == 'new':
            return operators.desc('_date')
        elif sort == 'old':
            return operators.asc('_date')
        elif sort == 'top':
            return operators.desc('_score')
        elif sort == 'controversial':
            return operators.desc('_controversy')

class CommentSortMenu(SortMenu):
    """Sort menu for comments pages"""
    options   = ('hot', 'new', 'controversial', 'top', 'old')

class SearchSortMenu(SortMenu):
    """Sort menu for search pages."""
    default   = 'relevance'
    mapping   = dict(relevance = None,
                     hot = 'hot desc',
                     new = 'date desc',
                     old = 'date asc',
                     top = 'points desc')
    options   = mapping.keys()

    @classmethod
    def operator(cls, sort):
        return cls.mapping.get(sort, cls.mapping[cls.default])

class RecSortMenu(SortMenu):
    """Sort menu for recommendation page"""
    default   = 'new'
    options   = ('hot', 'new', 'top', 'controversial', 'relevance')

class NewMenu(SimpleGetMenu):
    get_param = 'sort'
    default   = 'new'
    options   = ('new', 'rising')
    type = 'flatlist'

    def __init__(self, **kw):
        kw['title'] = _("Sort by")
        SimpleGetMenu.__init__(self, **kw)

    @classmethod
    def operator(self, sort):
        if sort == 'new':
            return operators.desc('_date')


class KindMenu(SimpleGetMenu):
    get_param = 'kind'
    default = 'all'
    options = ('links', 'comments', 'messages', 'all')

    def __init__(self, **kw):
        kw['title'] = _("Kind")
        SimpleGetMenu.__init__(self, **kw)

    def make_title(self, attr):
        if attr == "all":
            return _("All")
        return menu[attr]

class TimeMenu(SimpleGetMenu):
    """Menu for setting the time interval of the listing (from 'hour' to 'all')"""
    get_param = 't'
    default   = 'all'
    options   = ('hour', 'day', 'week', 'month', 'year', 'all')

    def __init__(self, **kw):
        kw.setdefault('title', _("Links from"))
        SimpleGetMenu.__init__(self, **kw)

    @classmethod
    def operator(self, time):
        from r2.models import Link
        if time != 'all':
            return Link.c._date >= timeago(time)

class NumCommentsMenu(SimpleGetMenu):
    """menu for toggling between the user's preferred number of
    comments and the max allowed in the display, assuming the number
    of comments in the listing exceeds one or both."""
    get_param = 'all'
    default   = 'false'
    options   = ('true', 'false')

    def __init__(self, num_comments, **context):
        context['title'] = _("Show") + ':'
        self.num_comments = num_comments
        SimpleGetMenu.__init__(self, **context)

    def make_title(self, attr):
        user_num = c.user.pref_num_comments
        if user_num > self.num_comments:
            # no menus needed if the number of comments is smaller
            # than any of the limits
            return ""
        elif self.num_comments > g.max_comments:
            # if the number present is larger than the global max,
            # label the menu as the user pref and the max number
            return dict(true=str(g.max_comments),
                        false=str(user_num))[attr]
        else:
            # if the number is less than the global max, display "all"
            # instead for the upper bound.
            return dict(true=_("All"),
                        false=str(user_num))[attr]


    def render(self, **kw):
        user_num = c.user.pref_num_comments
        if user_num > self.num_comments:
            return ""
        return SimpleGetMenu.render(self, **kw)

class SubredditMenu(NavMenu):
    def find_selected(self):
        """Always return False so the title is always displayed"""
        return None

class TagSortMenu(SimpleGetMenu):
    """Menu for listings by tag"""
    get_param = 'sort'
    default   = 'old'
    options   = ('old', 'new', 'top')

    def __init__(self, **kw):
        kw['title'] = _("Sort By") + ':'
        SimpleGetMenu.__init__(self, **kw)

    @classmethod
    def operator(self, sort):
        if sort == 'new':
            return operators.desc('_t1_date')
        elif sort == 'old':
            return operators.asc('_t1_date')
        elif sort == 'top':
            return operators.desc('_t1_score')

# --------------------
# TODO: move to admin area
class AdminReporterMenu(SortMenu):
    default = 'top'
    options = ('hot', 'new', 'top')

class AdminKindMenu(KindMenu):
    options = ('all', 'links', 'comments', 'spam', 'autobanned')


class AdminTimeMenu(TimeMenu):
    get_param = 't'
    default   = 'day'
    options   = ('hour', 'day', 'week')


