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

from copy import copy
import time, hashlib
from datetime import datetime

from geolocator import gislib
from pylons import c, g
from pylons.i18n import _
import sqlalchemy as sa

from r2.lib.db           import tdb_sql as tdb
from r2.lib.db.thing     import Thing, Relation, NotFound
from r2.lib.db.operators import lower
from r2.lib.db.userrel   import UserRel
from r2.lib.memoize      import memoize, clear_memo
from r2.lib.utils        import randstr
from r2.lib.strings      import strings, plurals
from r2.lib.base         import current_login_cookie
from r2.lib.rancode      import random_key


class AccountExists(Exception): pass
class NotEnoughKarma(Exception): pass

class Account(Thing):
    _data_int_props = Thing._data_int_props + ('report_made', 'report_correct',
                                               'report_ignored', 'spammer',
                                               'reported')
    _int_prop_prefixes = ('karma_',)
    _defaults = dict(pref_numsites = 10,
                     pref_frame = False,
                     pref_newwindow = False,
                     pref_public_votes = False,
                     pref_kibitz = False,
                     pref_hide_ups = False,
                     pref_hide_downs = True,
                     pref_min_link_score = -2,
                     pref_min_comment_score = -2,
                     pref_num_comments = g.num_comments,
                     pref_lang = 'en',
                     pref_content_langs = ('en',),
                     pref_over_18 = False,
                     pref_compress = False,
                     pref_organic = True,
                     pref_show_stylesheets = True,
                     pref_url = '',
                     pref_location = '',
                     pref_latitude = None,
                     pref_longitude = None,
                     pref_meetup_notify_enabled = False,
                     pref_meetup_notify_radius = 50,
                     pref_show_parent_comments = False,
                     email_validated = True,
                     confirmation_code = 'abcde',
                     reported = 0,
                     report_made = 0,
                     report_correct = 0,
                     report_ignored = 0,
                     spammer = 0,
                     sort_options = {},
                     has_subscribed = False,
                     pref_media = 'subreddit',
                     share = {},
                     messagebanned = False,
                     dashboard_visit = datetime(2006,10,1, tzinfo = g.tz)
                     )

    def karma_ups_downs(self, kind, sr = None):
        # NOTE: There is a legacy inconsistency in this method. If no subreddit
        # is specified, karma from all subreddits will be totaled, with each
        # scaled according to its karma multiplier before being summed. But if
        # a subreddit IS specified, the return value will NOT be scaled.

        assert kind in ('link', 'comment', 'adjustment')

        from subreddit import Subreddit  # prevent circular import

        # If getting karma for a single sr, it's easy
        if sr is not None:
            ups = getattr(self, 'karma_ups_{0}_{1}'.format(kind, sr.name), 0)
            downs = getattr(self, 'karma_downs_{0}_{1}'.format(kind, sr.name), 0)
            return (ups, downs)

        # Otherwise, loop through attributes and sum all karmas
        totals = [0, 0]
        for k, v in self._t.iteritems():
            for pre, idx in (('karma_ups_' + kind + '_', 0),
                              ('karma_downs_' + kind + '_', 1)):
                if k.startswith(pre):
                    karma_sr_name = k[len(pre):]
                    index = idx
                    break
            else:
                continue

            multiplier = 1
            if kind == 'link':
                try:
                    karma_sr = Subreddit._by_name(karma_sr_name)
                    multiplier = karma_sr.post_karma_multiplier
                except NotFound:
                    pass
            totals[index] += v * multiplier
        return tuple(totals)

    def karma(self, *args):
        ud = self.karma_ups_downs(*args)
        return ud[0] - ud[1]

    def percent_up(self):
        ups, downs = self.safe_karma_ups_downs

        if not downs:
            return 100.0
        else:
            return float(ups) / float(ups + downs) * 100

    def incr_karma(self, kind, sr, amt_up, amt_down):
        def do_incr(prop, amt):
            if hasattr(self, prop):
                self._incr(prop, amt)
            else:
                assert self._loaded
                setattr(self, prop, amt)
                self._commit()

        if amt_up:
            do_incr('karma_ups_{0}_{1}'.format(kind, sr.name), amt_up)
        if amt_down:
            do_incr('karma_downs_{0}_{1}'.format(kind, sr.name), amt_down)

        from r2.lib.user_stats import expire_user_change  # prevent circular import
        expire_user_change(self)

    @property
    def link_karma(self):
        return self.karma('link')

    @property
    def comment_karma(self):
        return self.karma('comment')

    @property
    def adjustment_karma(self):
        return self.karma('adjustment')

    @property
    def safe_karma_ups_downs(self):
        karmas = [self.karma_ups_downs(kind) for kind in 'link', 'comment', 'adjustment']
        return tuple(map(sum, zip(*karmas)))

    @property
    def safe_karma(self):
        pair = self.safe_karma_ups_downs
        karma = pair[0] - pair[1]
        return max(karma, 0) if karma > -1000 else karma

    @property
    def monthly_karma_ups_downs(self):
        from r2.lib.user_stats import cached_monthly_user_change
        return cached_monthly_user_change(self)

    @property
    def monthly_karma(self):
        ret = self.monthly_karma_ups_downs
        return ret[0] - ret[1]

    def downvote_cache_key(self, kind):
        """kind is 'link' or 'comment'"""
        return 'account_%d_%s_downvotes' % (self._id, kind)

    def check_downvote(self, vote_kind):
        """Checks whether this account has enough karma to cast a downvote.

        vote_kind is 'link' or 'comment' depending on the type of vote that's
        being cast.

        This makes the assumption that the user can't cast a vote for something
        on the non-current subreddit.
        """
        from r2.models.vote import Vote, Link, Comment

        def get_cached_downvotes(content_cls):
            kind = content_cls.__name__.lower()
            cache_key = self.downvote_cache_key(kind)
            downvotes = g.cache.get(cache_key)
            if downvotes is None:
                vote_cls = Vote.rel(Account, content_cls)

                # Get a count of content_cls downvotes
                type = tdb.rel_types_id[vote_cls._type_id]
                # rt = rel table
                # dt = data table
                # tt = thing table
                rt, account_tt, content_cls_tt, dt = type.rel_table

                cols = [ sa.func.count(rt.c.rel_id) ]
                where = sa.and_(rt.c.thing1_id == self._id, rt.c.name == '-1')
                query = sa.select(cols, where)
                downvotes = query.execute().scalar()

                g.cache.set(cache_key, downvotes)
            return downvotes

        link_downvote_karma = get_cached_downvotes(Link) * c.current_or_default_sr.post_karma_multiplier
        comment_downvote_karma = get_cached_downvotes(Comment)
        karma_spent = link_downvote_karma + comment_downvote_karma

        karma_balance = self.safe_karma * 4
        vote_cost = c.current_or_default_sr.post_karma_multiplier if vote_kind == 'link' else 1
        if karma_spent + vote_cost > karma_balance:
            points_needed = abs(karma_balance - karma_spent - vote_cost)
            msg = strings.not_enough_downvote_karma % (points_needed, plurals.N_points(points_needed))
            raise NotEnoughKarma(msg)

    def incr_downvote(self, delta, kind):
        """kind is link or comment"""
        try:
            g.cache.incr(self.downvote_cache_key(kind), delta)
        except ValueError, e:
            print 'Account.incr_downvote failed with: %s' % e

    def make_cookie(self, timestr = None, admin = False):
        if not self._loaded:
            self._load()
        timestr = timestr or time.strftime('%Y-%m-%dT%H:%M:%S')
        id_time = str(self._id) + ',' + timestr
        to_hash = ','.join((id_time, self.password, g.SECRET))
        if admin:
            to_hash += 'admin'
        return id_time + ',' + hashlib.sha1(to_hash).hexdigest()

    def needs_captcha(self):
        return self.safe_karma < 1

    def modhash(self):
        to_hash = ','.join((current_login_cookie(), g.SECRET))
        return hashlib.sha1(to_hash).hexdigest()
    
    def valid_hash(self, hash):
        return hash == self.modhash()

    @classmethod
    @memoize('account._by_name')
    def _by_name_cache(cls, name, allow_deleted = False):
        #relower name here, just in case
        deleted = (True, False) if allow_deleted else False
        q = cls._query(lower(Account.c.name) == name.lower(),
                       Account.c._spam == (True, False),
                       Account.c._deleted == deleted)

        q._limit = 1
        l = list(q)
        if l:
            return l[0]._id

    @classmethod
    def _by_name(cls, name, allow_deleted = False):
        #lower name here so there is only one cache
        uid = cls._by_name_cache(name.lower(), allow_deleted)
        if uid:
            return cls._byID(uid, True)
        else:
            raise NotFound, 'Account %s' % name

    @property
    def friends(self):
        return self.friend_ids()

    def delete(self):
        self._deleted = True
        self._commit()
        clear_memo('account._by_name', Account, self.name.lower(), False)
        
        #remove from friends lists
        q = Friend._query(Friend.c._thing2_id == self._id,
                          Friend.c._name == 'friend',
                          eager_load = True)
        for f in q:
            f._thing1.remove_friend(f._thing2)

    @property
    def subreddits(self):
        from subreddit import Subreddit
        return Subreddit.user_subreddits(self)

    @property
    def draft_sr_name(self):
      return self.name + "-drafts"

    @property
    def coords(self):
        if self.pref_latitude is not None and self.pref_longitude is not None:
            return (self.pref_latitude, self.pref_longitude)
        return None

    def is_within_radius(self, coords, radius):
        return self.coords is not None and \
            gislib.getDistance(self.coords, coords) <= radius

    def recent_share_emails(self):
        return self.share.get('recent', set([]))

    def add_share_emails(self, emails):
        if not emails:
            return
        
        if not isinstance(emails, set):
            emails = set(emails)

        self.share.setdefault('emails', {})
        share = self.share.copy()

        share_emails = share['emails']
        for e in emails:
            share_emails[e] = share_emails.get(e, 0) +1
            
        share['recent'] = emails

        self.share = share
        
            
            


class FakeAccount(Account):
    _nodb = True


def valid_cookie(cookie):
    try:
        uid, timestr, hash = cookie.split(',')
        uid = int(uid)
    except:
        return (False, False)

    try:
        account = Account._byID(uid, True)
        if account._deleted:
            return (False, False)
    except NotFound:
        return (False, False)

    if cookie == account.make_cookie(timestr, admin = False):
        return (account, False)
    elif cookie == account.make_cookie(timestr, admin = True):
        return (account, True)
    return (False, False)

def valid_login(name, password):
    try:
        a = Account._by_name(name)
    except NotFound:
        return False

    if not a._loaded: a._load()
    return valid_password(a, password)

def valid_password(a, password):
    try:
        if a.password == passhash(a.name, password, ''):
            #add a salt
            a.password = passhash(a.name, password, True)
            a._commit()
            return a
        else:
            salt = a.password[:3]
            if a.password == passhash(a.name, password, salt):
                return a
    except AttributeError:
        return False

def passhash(username, password, salt = ''):
    if salt is True:
        salt = randstr(3)
    tohash = '%s%s %s' % (salt, username, password)
    if isinstance(tohash, unicode):
        # Force tohash to be a byte string so it can be hashed
        tohash = tohash.encode('utf8')
    return salt + hashlib.sha1(tohash).hexdigest()

def change_password(user, newpassword):
    user.password = passhash(user.name, newpassword, True)
    user._commit()
    return True

#TODO reset the cache
def register(name, password, email):
    try:
        a = Account._by_name(name)
        raise AccountExists
    except NotFound:
        a = Account(name = name,
                    password = passhash(name, password, True))
        a.email = email

        a.confirmation_code = random_key(6)
        a.email_validated = False

        a._commit()

        from r2.lib.emailer      import confirmation_email
        confirmation_email(a)
            
        # Clear memoization of both with and without deleted
        clear_memo('account._by_name', Account, name.lower(), True)
        clear_memo('account._by_name', Account, name.lower(), False)
        return a

class Friend(Relation(Account, Account)): pass
Account.__bases__ += (UserRel('friend', Friend),)


