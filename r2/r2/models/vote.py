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
from __future__ import with_statement

from r2.lib.db.thing import MultiRelation, Relation, thing_prefix, cache
from r2.lib.utils import tup, timeago
from r2.lib.db.operators import ip_network
from r2.lib.normalized_hot import expire_hot
from r2.config.databases import tz

from account import Account
from link import Link, Comment
from subreddit import Subreddit

from datetime import timedelta, datetime

from pylons import g, c


def score_changes(amount, old_amount):
    uc = dc = 0
    a, oa = amount, old_amount
    if oa == 0 and a > 0: uc = a
    elif oa == 0 and a < 0: dc = -a
    elif oa > 0 and a == 0: uc = -oa
    elif oa < 0 and a == 0: dc = oa
    elif oa > 0 and a < 0: uc = -oa; dc = -a
    elif oa < 0 and a > 0: dc = oa; uc = a
    return uc, dc

class Vote(MultiRelation('vote',
                         Relation(Account, Link),
                         Relation(Account, Comment))):


    @classmethod
    def vote(cls, sub, obj, dir, ip, spam = False, organic = False):
        from admintools import valid_user, valid_thing, update_score
        from r2.lib.count import incr_counts

        # An account can only perform 1 voting operation at a time.
        with g.make_lock('account_%s_voting' % sub._id) as lock:
            kind = obj.__class__.__name__.lower()

            lock.log('voting checkpoint A')

            # If downvoting ensure that the user has enough karma, it
            # will raise an exception if not.
            if dir == False:
                sub.check_downvote(kind)

            lock.log('voting checkpoint B')

            # Do the voting.
            sr = obj.subreddit_slow
            karma = sub.karma(kind, sr)

            lock.log('voting checkpoint C')

            #check for old vote
            rel = cls.rel(sub, obj)
            oldvote = list(rel._query(rel.c._thing1_id == sub._id,
                                      rel.c._thing2_id == obj._id,
                                      data = True))

            amount = 1 if dir is True else 0 if dir is None else -1

            lock.log('voting checkpoint D')

            is_new = False
            #old vote
            if len(oldvote):
                v = oldvote[0]
                oldamount = int(v._name)
                v._name = str(amount)

                #these still need to be recalculated
                old_valid_thing = getattr(v, 'valid_thing', True)
                v.valid_thing = (valid_thing(v, karma)
                                 and v.valid_thing
                                 and not spam)
                v.valid_user = (v.valid_user
                                and v.valid_thing
                                and valid_user(v, sr, karma))
            #new vote
            else:
                is_new = True
                oldamount = 0
                v = rel(sub, obj, str(amount))
                v.author_id = obj.author_id
                v.ip = ip
                old_valid_thing = v.valid_thing = (valid_thing(v, karma) and
                                                   not spam)
                v.valid_user = v.valid_thing and valid_user(v, sr, karma)
                if organic:
                    v.organic = organic

            lock.log('voting checkpoint E')
            v._commit()
            lock.log('voting checkpoint F')

            # Record that this account has made a downvote.
            up_change, down_change = score_changes(amount, oldamount)
            if down_change:
                sub.incr_downvote(down_change, kind)

            lock.log('voting checkpoint G')

        # Release the lock since both the downvote count and the vote count
        # have been updated, and then continue by updating karmas.
        update_score(obj, up_change, down_change,
                     v.valid_thing, old_valid_thing)

        if v.valid_user:
            author = Account._byID(obj.author_id, data=True)
            author.incr_karma(kind, sr, up_change, down_change)

        #update the sr's valid vote count
        if is_new and v.valid_thing and kind == 'link':
            if sub._id != obj.author_id:
                incr_counts([sr])

        return v

    #TODO make this generic and put on multirelation?
    @classmethod
    def likes(cls, sub, obj):
        votes = cls._fast_query(sub, obj, ('1', '-1'), data=False)
        votes = dict((tuple(k[:2]), v) for k, v in votes.iteritems() if v)
        return votes


