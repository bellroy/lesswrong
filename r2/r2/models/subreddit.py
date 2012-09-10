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
from pylons import c, g
from pylons.i18n import _

from r2.lib.db.thing import Thing, Relation, NotFound
from account import Account
from printable import Printable
from r2.lib.db.userrel import UserRel
from r2.lib.db.operators import lower, or_, and_, desc
from r2.lib.memoize import memoize, clear_memo
from r2.lib.utils import tup
from r2.lib.strings import strings, Score
from r2.lib.filters import _force_unicode
from r2.models.image_holder import ImageHolder

import os.path
import random

class SubredditExists(Exception): pass

class Subreddit(Thing, Printable, ImageHolder):
    _defaults = dict(static_path = g.static_path,
                     stylesheet = None,
                     stylesheet_rtl = None,
                     stylesheet_contents = '',
                     stylesheet_hash     = '0',
                     firsttext = strings.firsttext,
                     header = None,
                     description = '',
                     images = {},
                     ad_file = os.path.join(g.static_path, 'ad_default.html'),
                     reported = 0,
                     valid_votes = 0,
                     show_media = False,
                     domain = None,
                     default_listing = 'hot',
                     post_karma_multiplier = g.post_karma_multiplier,
                     posts_per_page_multiplier = 1
                     )
    sr_limit = 50

    @classmethod
    def _new(self, name, title, lang = 'en', type = 'public',
             over_18 = False, **kw):
        try:
            sr = Subreddit._by_name(name)
            raise SubredditExists
        except NotFound:
            sr = Subreddit(name = name,
                           title = title,
                           lang = lang,
                           type = type,
                           over_18 = over_18,
                           **kw)
            sr._commit()
            clear_memo('subreddit._by_name', Subreddit, name.lower())
            clear_memo('subreddit.subreddits', Subreddit)
            return sr

    @classmethod
    def _create_and_subscribe(self, name, user, kw):
      # kw is expected to have been sanitised by the caller
      sr = Subreddit._new(name = name, **kw)
      Subreddit.subscribe_defaults(user)
      # make sure this user is on the admin list of that site!
      if sr.add_subscriber(user):
        sr._incr('_ups', 1)
      sr.add_moderator(user)
      sr.add_contributor(user)
      return sr

    @classmethod
    def default(cls):
      try:
        return cls._by_name(g.default_sr)
      except NotFound:
        return DefaultSR()

    @classmethod
    @memoize('subreddit._by_name')
    def _by_name_cache(cls, name):
        q = cls._query(lower(cls.c.name) == name.lower(),
                       cls.c._spam == (True, False),
                       limit = 1)
        l = list(q)
        if l:
            return l[0]._id

    @classmethod
    def _by_name(cls, name):
        #lower name here so there is only one cache
        name = name.lower()

        if name == 'friends':
            return Friends
        elif name == 'all':
            return All
        else:
            sr_id = cls._by_name_cache(name)
            if sr_id:
                return cls._byID(sr_id, True)
            else:
                raise NotFound, 'Subreddit %s' % name

    @classmethod
    @memoize('subreddit._by_domain')
    def _by_domain_cache(cls, name):
        q = cls._query(cls.c.domain == name,
                       cls.c.over_18 == (True, False),
                       limit = 1)
        l = list(q)
        if l:
            return l[0]._id

    @classmethod
    def _by_domain(cls, domain):
        sr_id = cls._by_domain_cache(_force_unicode(domain).lower())
        if sr_id:
            return cls._byID(sr_id, True)
        else:
            return None

    @property
    def moderators(self):
        return self.moderator_ids()

    @property
    def editors(self):
        return self.editor_ids()

    @property
    def contributors(self):
        return self.contributor_ids()

    @property
    def banned(self):
        return self.banned_ids()

    @property
    def subscribers(self):
        return self.subscriber_ids()

    def can_comment(self, user):
        if c.user_is_admin:
            return True
        elif self.is_banned(user):
            return False
        elif self.type in ('public','restricted'):
            return True
        elif self.is_moderator(user) or self.is_contributor(user):
            #private requires contributorship
            return True
        else:
            return False

    def can_submit(self, user):
        if c.user_is_admin:
            return True
        elif self.is_banned(user):
            return False
        elif self.is_moderator(user) or self.is_editor(user):
            # moderators and editors can always submit
            return True
        elif self == Subreddit._by_name('discussion') and user.safe_karma < g.discussion_karma_to_post:
            return False
        elif self.type == 'public':
            return True
        elif self.is_contributor(user):
            #restricted/private require contributorship
            return True
        elif self == Subreddit._by_name(g.default_sr) and user.safe_karma >= g.karma_to_post:
            return True
        else:
            return False

    def can_ban(self,user):
        return (user
                and (c.user_is_admin
                     or self.is_moderator(user)))

    def can_change_stylesheet(self, user):
        if c.user_is_loggedin:
            return c.user_is_admin or self.is_moderator(user)
        else:
            return False

    def is_special(self, user):
        return (user
                and (c.user_is_admin
                     or self.is_moderator(user)
                     or (self.type in ('restricted', 'private')
                         and self.is_contributor(user))))

    def can_give_karma(self, user):
        return self.is_special(user)

    def should_ratelimit(self, user, kind):
        if c.user_is_admin:
            return False

        if kind == 'comment':
            rl_karma = g.MIN_RATE_LIMIT_COMMENT_KARMA
        else:
            rl_karma = g.MIN_RATE_LIMIT_KARMA

        return not (self.is_special(user) or
                    user.karma(kind, self) >= rl_karma)

    def can_view(self, user):
        if c.user_is_admin:
            return True

        if self.type in ('public', 'restricted'):
            return True
        elif c.user_is_loggedin:
            #private requires contributorship
            return self.is_contributor(user) or self.is_moderator(user)

    @classmethod
    def load_subreddits(cls, links, return_dict = True):
        """returns the subreddits for a list of links. it also preloads the
        permissions for the current user."""
        srids = set(l.sr_id for l in links if hasattr(l, "sr_id"))
        subreddits = {}
        if srids:
            subreddits = cls._byID(srids, True)

        if subreddits and c.user_is_loggedin:
            # dict( {Subreddit,Account,name} -> Relationship )
            SRMember._fast_query(subreddits.values(), (c.user,),
                                 ('subscriber','contributor','moderator'))

        return subreddits if return_dict else subreddits.values()

    #rising uses this to know which subreddits to include, doesn't
    #work for all/friends atm
    def rising_srs(self):
        if c.default_sr or not hasattr(self, '_id'):
            user = c.user if c.user_is_loggedin else None
            sr_ids = self.user_subreddits(user)
        else:
            sr_ids = (self._id,)
        return sr_ids

    def get_links(self, sort, time, link_cls = None):
        from r2.lib.db import queries
        from r2.models import Link

        if not link_cls:
            link_cls = Link
        return queries.get_links(self, sort, time, link_cls)

    def get_comments(self, sort, time):
        """This method relies on the fact that Link and Comment can be
          queried with the same filters"""
        from r2.models import Comment
        return self.get_links(sort, time, Comment)

    @classmethod
    def add_props(cls, user, wrapped):
        names = ('subscriber', 'moderator', 'contributor')
        rels = (SRMember._fast_query(wrapped, [user], names) if user else {})
        defaults = Subreddit.default_srs(c.content_langs, ids = True)
        for item in wrapped:
            if not user or not user.has_subscribed:
                item.subscriber = item._id in defaults
            else:
                item.subscriber = rels.get((item, user, 'subscriber'))
            item.moderator = rels.get((item, user, 'moderator'))
            item.contributor = item.moderator or \
                rels.get((item, user, 'contributor'))
            item.score = item._ups
            item.score_fmt = Score.subscribers

    #TODO: make this work
    @staticmethod
    def cache_key(wrapped):
        if c.user_is_admin:
            return False

        s = (str(i) for i in (wrapped._fullname,
                              bool(c.user_is_loggedin),
                              wrapped.subscriber,
                              wrapped.moderator,
                              wrapped.contributor,
                              wrapped._spam))
        s = ''.join(s)
        return s

    #TODO: make this work
    #@property
    #def author_id(self):
        #return 1

    @classmethod
    def default_srs(cls, lang, ids = False, limit = None):
        """Returns the default list of subreddits for a given language, sorted
        by popularity"""
        pop_reddits = Subreddit._query(Subreddit.c.type == ('public', 'restricted'),
                                       sort=desc('_downs'),
                                       limit = limit,
                                       data = True,
                                       read_cache = True,
                                       write_cache = True,
                                       cache_time = g.page_cache_time)
        if lang != 'all':
            pop_reddits._filter(Subreddit.c.lang == lang)

        if not c.over18:
            pop_reddits._filter(Subreddit.c.over_18 == False)

        pop_reddits._filter(Subreddit.c.name != 'discussion')

        pop_reddits = list(pop_reddits)

        if not pop_reddits and lang != 'en':
            pop_reddits = cls.default_srs('en')

        return [s._id for s in pop_reddits] if ids else list(pop_reddits)

    @classmethod
    def user_subreddits(cls, user, limit = sr_limit):
        """subreddits that appear in a user's listings. returns the default
        srs if there are no subscriptions."""
        if user and user.has_subscribed:
            sr_ids = Subreddit.reverse_subscriber_ids(user)
            if limit and len(sr_ids) > limit:
                return random.sample(sr_ids, limit)
            else:
                return sr_ids
        else:
            return cls.default_srs(c.content_langs, ids = True)

    def is_subscriber_defaults(self, user):
        if user.has_subscribed:
            return self.is_subscriber(user)
        else:
            return self in self.default_srs(c.content_langs)

    @classmethod
    def subscribe_defaults(cls, user):
        if not user.has_subscribed:
            for sr in Subreddit.default_srs(c.content_langs):
                if sr.add_subscriber(c.user):
                    sr._incr('_ups', 1)
            user.has_subscribed = True
            user._commit()

    @classmethod
    def submit_sr(cls, user):
        """subreddit names that appear in a user's submit page. basically a
        sorted/rearranged version of user_subreddits()."""
        sub_ids = cls.user_subreddits(user, False)
        srs = Subreddit._byID(sub_ids, True,
                              return_dict = False)
        srs = [s for s in srs if s.can_submit(user) or s.name == g.default_sr]

        # Add the discussion subreddit manually. Need to do this because users
        # are not subscribed to it.
        try:
            discussion_sr = Subreddit._by_name('discussion')
            if discussion_sr._id not in sub_ids and discussion_sr.can_submit(user):
                srs.insert(0, discussion_sr)
        except NotFound:
          pass

        srs.sort(key=lambda a:a.title)
        return srs

    @property
    def path(self):
        return "/r/%s/" % self.name


    def keep_item(self, wrapped):
        if c.user_is_admin:
            return True

        user = c.user if c.user_is_loggedin else None
        return self.can_view(user)

class FakeSubreddit(Subreddit):
    over_18 = False
    _nodb = True

    def __init__(self):
        Subreddit.__init__(self)
        self.title = ''

    def is_moderator(self, user):
        return c.user_is_loggedin and c.user_is_admin

    def can_view(self, user):
        return True

    def can_comment(self, user):
        return False

    def can_submit(self, user):
        return False

    def can_change_stylesheet(self, user):
        return False

    def is_banned(self, user):
        return False

class FriendsSR(FakeSubreddit):
    name = 'friends'
    title = 'Friends'

    def get_links(self, sort, time, link_cls = None):
        from r2.lib.db import queries
        from r2.models import Link
        from r2.controllers.errors import UserRequiredException

        if not c.user_is_loggedin:
            raise UserRequiredException

        if not link_cls:
            link_cls = Link

        q = link_cls._query(self.c.author_id == c.user.friends,
                        sort = queries.db_sort(sort))
        if time != 'all':
            q._filter(queries.db_times[time])
        return q

class AllSR(FakeSubreddit):
    name = 'all'
    title = 'All'

    def get_links(self, sort, time, link_cls = None):
        from r2.models import Link
        from r2.lib.db import queries

        if not link_cls:
            link_cls = Link
        q = link_cls._query(sort = queries.db_sort(sort))
        if time != 'all':
            q._filter(queries.db_times[time])
        return q


class DefaultSR(FakeSubreddit):
    #notice the space before reddit.com
    name = g.default_sr
    path = '/'
    header = '/static/logo_trans.png'

    def get_links_sr_ids(self, sr_ids, sort, time, link_cls = None):
        from r2.lib.db import queries
        from r2.models import Link

        if not link_cls:
            link_cls = Link

        if not sr_ids:
            srs = []
        else:
            srs = Subreddit._byID(sr_ids, return_dict = False)

        if g.use_query_cache:
            results = []
            for sr in srs:
                results.append(queries.get_links(sr, sort, time))
            return queries.merge_cached_results(*results)
        else:
            q = link_cls._query(link_cls.c.sr_id == sr_ids,
                            sort = queries.db_sort(sort))
            if sort == 'toplinks':
                q._filter(link_cls.c.top_link == True)
            elif sort == 'blessed':
                q._filter(link_cls.c.blessed == True)
            if time != 'all':
                q._filter(queries.db_times[time])
            return q

    def get_links(self, sort, time, link_cls = None):
        user = c.user if c.user_is_loggedin else None
        sr_ids = Subreddit.user_subreddits(user)
        return self.get_links_sr_ids(sr_ids, sort, time, link_cls)

    @property
    def title(self):
        return _(g.front_page_title)

    @property
    def default_listing(self):
        return 'blessed'

class MultiReddit(DefaultSR):
    name = 'multi'

    def __init__(self, sr_ids, path):
        DefaultSR.__init__(self)
        self.real_path = path
        self.sr_ids = sr_ids

    @property
    def path(self):
        return '/r/' + self.real_path

    def get_links(self, sort, time, link_cls = None):
        return self.get_links_sr_ids(self.sr_ids, sort, time, link_cls)

class SubSR(DefaultSR):
    stylesheet = 'subreddit.css'
    #this will make the javascript not send an SR parameter
    name = ''

    def can_view(self, user):
        return True

    def can_comment(self, user):
        return False

    def can_submit(self, user):
        return True

    @property
    def path(self):
        return "/categories/"

class DomainSR(FakeSubreddit):
    @property
    def path(self):
        return '/domain/' + self.domain

    def __init__(self, domain):
        FakeSubreddit.__init__(self)
        self.domain = domain
        self.name = domain
        self.title = domain + ' ' + _('on lesswrong.com')

    def get_links(self, sort, time, link_cls = None):
        from r2.lib.db import queries
        return queries.get_domain_links(self.domain, sort, time)

Sub = SubSR()
Friends = FriendsSR()
All = AllSR()
Default = DefaultSR()

class SRMember(Relation(Subreddit, Account)): pass
Subreddit.__bases__ += (UserRel('moderator', SRMember),
                        UserRel('editor', SRMember),
                        UserRel('contributor', SRMember),
                        UserRel('subscriber', SRMember),
                        UserRel('banned', SRMember))
