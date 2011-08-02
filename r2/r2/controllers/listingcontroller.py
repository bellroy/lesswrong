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
from reddit_base import RedditController, base_listing
from validator import *

from r2.models import *
from r2.lib.pages import *
from r2.lib.menus import NewMenu, TimeMenu, SortMenu, RecSortMenu, TagSortMenu
from r2.lib.rising import get_rising
from r2.lib.wrapped import Wrapped
from r2.lib.normalized_hot import normalized_hot, get_hot
from r2.lib.recommendation import get_recommended
from r2.lib.db.thing import Query, Merge, Relations
from r2.lib.db import queries
from r2.lib.strings import Score
from r2.lib import organic
from r2.lib.solrsearch import SearchQuery
from r2.lib.utils import iters, check_cheating
from r2.lib.filters import _force_unicode

from admin import admin_profile_query

from pylons.i18n import _

import random

class ListingController(RedditController):
    """Generalized controller for pages with lists of links."""

    # toggle skipping of links based on the users' save/hide/vote preferences
    skip = True

    # toggles showing numbers
    show_nums = True

    # any text that should be shown on the top of the page
    infotext = None

    # builder class to use to generate the listing. if none, we'll try
    # to figure it out based on the query type
    builder_cls = None

    # page title
    title_text = ''

    # login box, subreddit box, submit box, etc, visible
    show_sidebar = True

    # class (probably a subclass of Reddit) to use to render the page.
    render_cls = Reddit

    #extra parameters to send to the render_cls constructor
    render_params = {}

    _link_listings = None

    # Robot (search engine) directives
    robots = None

    @classmethod
    def link_listings(cls, key = None):
        # This is done to defer generation of the dictionary until after
        # the classes have been defined
        if not cls._link_listings:
            cls._link_listings = {
                'blessed'       : BlessedController,
                'hot'           : HotController,
                'new'           : NewController,
                'top'           : ToplinksController,
                'controversial' : BrowseController,
            }

        return cls._link_listings if not key else cls._link_listings[key]

    @classmethod
    def listing_names(cls):
        return sorted(cls.link_listings().keys())

    @property
    def menus(self):
        """list of menus underneat the header (e.g., sort, time, kind,
        etc) to be displayed on this listing page"""
        return []

    @property
    def top_filter(self):
      return None

    @property
    def header_sub_nav(self):
      buttons = []
      if c.default_sr:
        buttons.append(NamedButton("promoted"))
        buttons.append(NamedButton("new"))
      else:
        buttons.append(NamedButton("new", aliases = ["/"]))

      buttons.append(NamedButton('top'))
      if c.user_is_loggedin:
        buttons.append(NamedButton('saved'))
      return buttons

    @base_listing
    def build_listing(self, num, after, reverse, count):
        """uses the query() method to define the contents of the
        listing and renders the page self.render_cls(..).render() with
        the listing as contents"""
        self.num = num
        self.count = count
        self.after = after
        self.reverse = reverse

        if after is not None:
            self.robots = "noindex,follow"

        self.query_obj = self.query()
        self.builder_obj = self.builder()
        self.listing_obj = self.listing()
        content = self.content()
        res =  self.render_cls(content = content,
                               show_sidebar = self.show_sidebar,
                               nav_menus = self.menus,
                               title = self.title(),
                               infotext = self.infotext,
                               robots = self.robots,
                               top_filter = self.top_filter,
                               header_sub_nav = self.header_sub_nav,
                               **self.render_params).render()
        return res


    def content(self):
        """Renderable object which will end up as content of the render_cls"""
        return self.listing_obj

    def query(self):
        """Query to execute to generate the listing"""
        raise NotImplementedError

    def builder(self):
        #store the query itself so it can be used elsewhere
        if self.builder_cls:
            builder_cls = self.builder_cls
        elif isinstance(self.query_obj, Query):
            builder_cls = QueryBuilder
        elif isinstance(self.query_obj, SearchQuery):
            builder_cls = SearchBuilder
        elif isinstance(self.query_obj, iters):
            builder_cls = IDBuilder
        elif isinstance(self.query_obj, queries.CachedResults):
            builder_cls = IDBuilder

        b = builder_cls(self.query_obj,
                        num = self.num,
                        skip = self.skip,
                        after = self.after,
                        count = self.count,
                        reverse = self.reverse,
                        wrap = self.builder_wrapper)

        return b

    def listing(self):
        """Listing to generate from the builder"""
        listing = LinkListing(self.builder_obj, show_nums = self.show_nums)
        return listing.listing()

    def title(self):
        """Page <title>"""
        return "%s - %s" % (self.title_text, c.site.title)

    def rightbox(self):
        """Contents of the right box when rendering"""
        pass

    @staticmethod
    def builder_wrapper(thing):
        w = Wrapped(thing)

        if isinstance(thing, Link):
            if thing.promoted:
                w = Wrapped(thing)
                w.render_class = PromotedLink
                w.rowstyle = 'promoted link'

            elif c.user.pref_compress:
                w.render_class = LinkCompressed
                w.score_fmt = Score.points

        return w

    def GET_listing(self, **env):
        return self.build_listing(**env)

class FixListing(object):
    """When sorting by hotness, computing a listing when the before/after
    link has a hottness of 0 is very slow. This class avoids drawing
    next/prev links when that will happen."""
    fix_listing = True

    def listing(self):
        listing = ListingController.listing(self)

        if not self.fix_listing:
            return listing

        #404 existing bad pages
        if self.after and self.after._hot == 0:
            self.abort404()

        #don't draw next/prev links for
        if listing.things:
            if listing.things[-1]._hot == 0:
                listing.next = None

            if listing.things[0]._hot == 0:
                listing.prev = None

        return listing

class HotController(FixListing, ListingController):
    where = 'hot'
    title_text = _('Popular articles')

    def organic(self):
        o_links, pos, calculation_key = organic.organic_links(c.user)
        if o_links:
            # get links in proximity to pos
            l = min(len(o_links) - 3, 8)
            disp_links = [o_links[(i + pos) % len(o_links)] for i in xrange(-2, l)]

            b = IDBuilder(disp_links, wrap = self.builder_wrapper)
            o = OrganicListing(b,
                               org_links = o_links,
                               visible_link = o_links[pos],
                               max_num = self.listing_obj.max_num,
                               max_score = self.listing_obj.max_score).listing()

            if len(o.things) > 0:
                # only pass through a listing if the links made it
                # through our builder
                organic.update_pos(pos+1, calculation_key)

                return o


    def query(self):
        #no need to worry when working from the cache
        if g.use_query_cache or c.site == Default:
            self.fix_listing = False

        if c.site == Default:
            user = c.user if c.user_is_loggedin else None
            sr_ids = Subreddit.user_subreddits(user)
            return normalized_hot(sr_ids)
        #if not using the query_cache we still want cached front pages
        elif (not g.use_query_cache
              and not isinstance(c.site, FakeSubreddit)
              and self.after is None
              and self.count == 0):
            return [l._fullname for l in get_hot(c.site)]
        else:
            return c.site.get_links('hot', 'all')

    def content(self):
        return self.listing_obj

    def GET_listing(self, **env):
        self.infotext = request.get.get('deleted') and strings.user_deleted
        return ListingController.GET_listing(self, **env)

class SavedController(ListingController):
    where = 'saved'
    skip = False
    title_text = _('Saved')

    def query(self):
        return queries.get_saved(c.user, not c.user_is_admin)

    @validate(VUser())
    def GET_listing(self, **env):
        return ListingController.GET_listing(self, **env)

class ToplinksController(ListingController):
    where = 'toplinks'
    title_text = _('Top scoring links')

    def query(self):
        return c.site.get_links('toplinks', 'all')

    def GET_listing(self, **env):
        return ListingController.GET_listing(self, **env)

class BlessedController(ListingController):
    where = 'blessed'

    def query(self):
        return c.site.get_links('blessed', 'all')

    def title(self):
        return c.site.title

    def GET_listing(self, **env):
        return ListingController.GET_listing(self, **env)

# This used to be RootController, but renamed since there is a new root controller
class PromotedController(ListingController):
   def __before__(self):
       ListingController.__before__(self)
       controller = self.link_listings(c.site.default_listing)
       self.__class__ = controller

class NewController(ListingController):
    where = 'new'
    title_text = _('Newest Submissions')

    def query(self):
        return c.site.get_links('new', 'all')

    def GET_listing(self, **env):
        return ListingController.GET_listing(self, **env)

class RecentpostsController(NewController):
    where = 'recentposts'
    title_text = _('Recent Posts')

    @staticmethod
    def builder_wrapper(thing):
        w = Wrapped(thing)

        if isinstance(thing, Link):
            w.render_class = InlineArticle

        return w

    def content(self):
        return RecentArticlesPage(content=self.listing_obj)

    def GET_listing(self, **env):
        if not env.has_key('limit'):
            env['limit'] = 250
        return NewController.GET_listing(self, **env)

class TagController(ListingController):
    where = 'tag'
    title_text = _('Articles Tagged')

    @property
    def menus(self):
        return [TagSortMenu(default = self.sort)]

    def query(self):
        q = LinkTag._query(LinkTag.c._thing2_id == self._tag._id,
                           LinkTag.c._name == 'tag',
                           LinkTag.c._t1_deleted == False,
                           sort = TagSortMenu.operator(self.sort),
                           eager_load = True,
                           thing_data = not g.use_query_cache
                      )
        q.prewrap_fn = lambda x: x._thing1
        return q

    def builder(self):
        b = SubredditTagBuilder(self.query_obj,
                                num = self.num,
                                skip = self.skip,
                                after = self.after,
                                count = self.count,
                                reverse = self.reverse,
                                wrap = self.builder_wrapper,
                                sr_ids = [c.current_or_default_sr._id])
        return b

    @validate(tag = VTagByName('tag'), sort = VMenu('where', TagSortMenu))
    def GET_listing(self, tag, sort, **env):
        self._tag = tag
        self.sort = sort
        TagController.title_text = _('Articles Tagged') + u' \N{LEFT SINGLE QUOTATION MARK}' + unicode(tag.name) + u'\N{RIGHT SINGLE QUOTATION MARK}'
        return ListingController.GET_listing(self, **env)

class BrowseController(ListingController):
    where = 'browse'

    @property
    def top_filter(self):
        return TimeMenu(default = self.time, title = _('Filter'), type='dropdown2')

    def query(self):
        return c.site.get_links(self.sort, self.time)

    # TODO: this is a hack with sort.
    @validate(sort = VOneOf('sort', ('top', 'controversial')),
              time = VMenu('where', TimeMenu))
    def GET_listing(self, sort, time, **env):
        self.sort = sort
        if sort == 'top':
            self.title_text = _('Top scoring articles')
        elif sort == 'controversial':
            self.title_text = _('Most controversial articles')
        self.time = time
        return ListingController.GET_listing(self, **env)


class RandomrisingController(ListingController):
    where = 'randomrising'
    title_text = _('You\'re really bored now, eh?')

    def query(self):
        links = get_rising(c.site)

        if not links:
            # just pull from the new page if the rising page isn't
            # populated for some reason
            links = c.site.get_links('new', 'all')
            if isinstance(links, Query):
                links._limit = 200
                links = [x._fullname for x in links]

        random.shuffle(links)

        return links

class EditsController(ListingController):
    title_text = _('Recent Edits')

    def query(self):
        return Edit._query(sort = desc('_date'))


class MeetupslistingController(ListingController):
    title_text = _('Upcoming Meetups')
    render_cls = MeetupIndexPage

    @property
    def header_sub_nav(self):
	    return []

    def query(self):
        return Meetup.upcoming_meetups_by_timestamp()

class ByIDController(ListingController):
    title_text = _('API')

    def query(self):
        return self.names

    @validate(names = VLinkFullnames("names"))
    def GET_listing(self, names, **env):
        if not names:
            return self.abort404()
        self.names = names
        return ListingController.GET_listing(self, **env)


class RecommendedController(ListingController):
    where = 'recommended'
    title_text = _('Recommended for you')

    @property
    def menus(self):
        return [RecSortMenu(default = self.sort)]

    def query(self):
        return get_recommended(c.user._id, sort = self.sort)

    @validate(VUser(),
              sort = VMenu("controller", RecSortMenu))
    def GET_listing(self, sort, **env):
        self.sort = sort
        return ListingController.GET_listing(self, **env)

class UserController(ListingController):
    render_cls = ProfilePage
    skip = False
    show_nums = False

    def title(self):
        titles = {'overview': _("Overview for %(user)s - %(site)s"),
                  'comments': _("Comments by %(user)s - %(site)s"),
                  'submitted': _("Submitted by %(user)s - %(site)s"),
                  'liked': _("Liked by %(user)s - %(site)s"),
                  'disliked': _("Disliked by %(user)s - %(site)s"),
                  'hidden': _("Hidden by %(user)s - %(site)s"),
                  'drafts': _("Drafts for %(user)s - %(site)s")}
        title = titles.get(self.where, _('Profile for %(user)s - %(site)s')) \
            % dict(user = _force_unicode(self.vuser.name), site = c.site.title)
        return title

    def query(self):
        q = None
        if self.where == 'overview':
            self.check_modified(self.vuser, 'overview')
            q = queries.get_overview(self.vuser, 'new', 'all')

        elif self.where == 'comments':
            self.check_modified(self.vuser, 'commented')
            q = queries.get_comments(self.vuser, 'new', 'all')

        elif self.where == 'submitted':
            self.check_modified(self.vuser, 'submitted')
            q = queries.get_submitted(self.vuser, 'new', 'all')

        elif self.where in ('liked', 'disliked'):
            self.check_modified(self.vuser, self.where)
            if self.where == 'liked':
                q = queries.get_liked(self.vuser, not c.user_is_admin)
            else:
                q = queries.get_disliked(self.vuser, not c.user_is_admin)

        elif self.where == 'hidden':
            q = queries.get_hidden(self.vuser, not c.user_is_admin)

        elif self.where == 'drafts':
            q = queries.get_drafts(self.vuser)

        elif c.user_is_admin:
            q = admin_profile_query(self.vuser, self.where, desc('_date'))

        if q is None:
            return self.abort404()

        return q

    @validate(vuser = VExistingUname('username'))
    def GET_listing(self, where, vuser, **env):
        self.where = where

        # the validator will ensure that vuser is a valid account
        if not vuser:
            return self.abort404()

        # pretend deleted users don't exist (although they are in the db still)
        if vuser._deleted:
            return self.abort404()

        # hide spammers profile pages
        if (not c.user_is_loggedin or
            (c.user._id != vuser._id and not c.user_is_admin)) \
               and vuser._spam:
            return self.abort404()

        if (where not in ('overview', 'submitted', 'comments')
            and not votes_visible(vuser)):
            return self.abort404()

        check_cheating('user')

        self.vuser = vuser
        self.render_params = {'user' : vuser}
        c.profilepage = True

        return ListingController.GET_listing(self, **env)


class MessageController(ListingController):
    show_sidebar = True
    render_cls = MessagePage

    def title(self, where = None):
        if where is None:
            where = self.where
        return "%s: %s - %s" % (_('Messages'), _(where.title()), c.site.title)

    @staticmethod
    def builder_wrapper(thing):
        if isinstance(thing, Comment):
            p = thing.make_permalink_slow()
            f = thing._fullname
            w = Wrapped(thing)
            w.render_class = Message
            w.to_id = c.user._id
            w.subject = _('Comment Reply')
            w.was_comment = True
            w.permalink, w._fullname = p, f
            return w
        else:
            return ListingController.builder_wrapper(thing)

    def query(self):
        if self.where == 'inbox':
            q = queries.get_inbox(c.user)

            #reset the inbox
            if c.have_messages:
                c.user.msgtime = False
                c.user._commit()

        elif self.where == 'sent':
            q = queries.get_sent(c.user)

        return q

    @validate(VUser())
    def GET_listing(self, where, **env):
        self.where = where
        c.msg_location = where
        return ListingController.GET_listing(self, **env)

    @validate(VUser(),
              to = nop('to'),
              subject = nop('subject'),
              message = nop('message'),
              success = nop('success'))
    def GET_compose(self, to, subject, message, success):
        captcha = Captcha() if c.user.needs_captcha() else None
        content = MessageCompose(to = to, subject = subject,
                                 captcha = captcha,
                                 message = message,
                                 success = success)
        return MessagePage(content = content, title = self.title('compose')).render()

class RedditsController(ListingController):
    render_cls = SubredditsPage

    def title(self):
        return _('Categories')

    def query(self):
        if self.where == 'banned' and c.user_is_admin:
            reddits = Subreddit._query(Subreddit.c._spam == True,
                                       sort = desc('_date'))
        else:
            reddits = Subreddit._query()
            if self.where == 'new':
                reddits._sort = desc('_date')
            else:
                reddits._sort = desc('_downs')
            if c.content_langs != 'all':
                reddits._filter(Subreddit.c.lang == c.content_langs)
            if not c.over18:
                reddits._filter(Subreddit.c.over_18 == False)

        return reddits
    def GET_listing(self, where, **env):
        self.where = where
        return ListingController.GET_listing(self, **env)

class MyredditsController(ListingController):
    render_cls = MySubredditsPage

    @property
    def menus(self):
        buttons = (NavButton(plurals.subscriber,  'subscriber'),
                    NavButton(plurals.contributor, 'contributor'),
                    NavButton(plurals.moderator,   'moderator'))

        return [NavMenu(buttons, base_path = '/categories/mine/', default = 'subscriber', type = "flatlist")]

    def title(self):
        return _('Categories: ') + self.where

    def query(self):
        reddits = SRMember._query(SRMember.c._name == self.where,
                                  SRMember.c._thing2_id == c.user._id,
                                  #hack to prevent the query from
                                  #adding it's own date
                                  sort = (desc('_t1_ups'), desc('_t1_date')),
                                  eager_load = True,
                                  thing_data = True)
        reddits.prewrap_fn = lambda x: x._thing1
        return reddits

    def content(self):
        user = c.user if c.user_is_loggedin else None
        num_subscriptions = len(Subreddit.reverse_subscriber_ids(user))
        if self.where == 'subscriber' and num_subscriptions == 0:
            message = strings.sr_messages['empty']
        else:
            message = strings.sr_messages.get(self.where)

        stack = PaneStack()

        if message:
            stack.append(InfoBar(message=message))

        stack.append(self.listing_obj)

        return stack

    @validate(VUser())
    def GET_listing(self, where, **env):
        self.where = where
        return ListingController.GET_listing(self, **env)

class CommentsController(ListingController):
    title_text = _('Comments')
    builder_cls = UnbannedCommentBuilder

    @property
    def header_sub_nav(self):
	    return [NamedButton("newcomments", dest="comments"), NamedButton("topcomments")]

    def query(self):
        q = Comment._query(Comment.c._spam == (True,False),
                           Comment.c.sr_id == c.current_or_default_sr._id,
                           sort = desc('_date'), data = True)
        if not c.user_is_admin:
            q._filter(Comment.c._spam == False)

        return q

    def builder(self):
        b = self.builder_cls(self.query_obj,
                             num = self.num,
                             skip = self.skip,
                             after = self.after,
                             count = self.count,
                             reverse = self.reverse,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id])
        return b


    def content(self):
        ps = PaneStack()
        ps.append(CommentReplyBox())
        ps.append(self.listing_obj)
        return ps

    def GET_listing(self, **env):
        c.full_comment_listing = True
        if not env.has_key('limit'):
            env['limit'] = 2 * c.user.pref_numsites
        return ListingController.GET_listing(self, **env)

class TopcommentsController(CommentsController):
	title_text = _('Top Comments')
	builder_cls = UnbannedCommentBuilder

	def query(self):
		q = Comment._query(Comment.c._spam == (True,False),
				Comment.c.sr_id == c.current_or_default_sr._id,
				sort = desc('_ups'), data = True)
		if not c.user_is_admin:
			q._filter(Comment.c._spam == False)

		if self.time != 'all':
			q._filter(queries.db_times[self.time])

		return q

	@property
	def top_filter(self):
		return TimeMenu(default = self.time, title = _('Filter'), type='dropdown2')

	@validate(time = VMenu('where', TimeMenu))
	def GET_listing(self, time, **env):
		self.time = time
		return CommentsController.GET_listing(self, **env)
