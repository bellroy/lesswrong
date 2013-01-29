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
from collections import defaultdict
from datetime import datetime, timedelta

import sqlalchemy as sa
from r2.models import Account, Vote, Link, Subreddit, Comment, KarmaAdjustment
from r2.lib.db import tdb_sql as tdb
from r2.lib import utils
import time

from pylons import g 
cache = g.cache

SECONDS_PER_MONTH = 86400 * 30
NUM_TOP_USERS = 15
CACHE_EXPIRY = 3600


def subreddits_with_custom_karma_multiplier():
    type = tdb.types_id[Subreddit._type_id]
    tt, dt = type.thing_table, type.data_table[0]

    aliases = tdb.alias_generator()
    karma = dt.alias(aliases.next())

    q = sa.select(
        [tt.c.thing_id],
        sa.and_(tt.c.spam == False,
              tt.c.deleted == False,
              karma.c.thing_id == tt.c.thing_id,
              karma.c.key == 'post_karma_multiplier'),
        group_by = [tt.c.thing_id],
    )

    sr_ids = [r.thing_id for r in q.execute().fetchall()]
    return Subreddit._byID(sr_ids, True, return_dict = False)


def karma_sr_weight_cases(table):
    key = table.c.key
    value_int = sa.cast(table.c.value, sa.Integer)
    cases = []

    for subreddit in subreddits_with_custom_karma_multiplier():
        mult = subreddit.post_karma_multiplier
        cases.append((key == 'karma_ups_link_' + subreddit.name, value_int * mult))
        cases.append((key == 'karma_downs_link_' + subreddit.name, value_int * -mult))
    cases.append((key.like('karma_ups_link_%'), value_int * g.post_karma_multiplier))
    cases.append((key.like('karma_downs_link_%'), value_int * -g.post_karma_multiplier))
    cases.append((key.like('karma_ups_%'), value_int))
    cases.append((key.like('karma_downs_%'), value_int * -1))
    return sa.case(cases, else_ = 0)


def top_users():
    type = tdb.types_id[Account._type_id]
    tt, dt = type.thing_table, type.data_table[0]

    aliases = tdb.alias_generator()
    account_data = dt.alias(aliases.next())

    s = sa.select(
        [tt.c.thing_id],
        sa.and_(tt.c.spam == False,
                tt.c.deleted == False,
                account_data.c.thing_id == tt.c.thing_id,
                account_data.c.key.like('karma_%')),
        group_by = [tt.c.thing_id],
        order_by = sa.desc(sa.func.sum(karma_sr_weight_cases(account_data))),
        limit = NUM_TOP_USERS)
    rows = s.execute().fetchall()
    return [r.thing_id for r in rows]


# Calculate the karma change for the given period and/or user
# TODO:  handle deleted users, spam articles and deleted articles, (and deleted comments?)
def all_user_change(*args, **kwargs):
    ret = defaultdict(lambda: (0, 0))

    for meth in user_vote_change_links, user_vote_change_comments, user_karma_adjustments:
        for aid, karma in meth(*args, **kwargs):
            karma_old = ret[aid]
            ret[aid] = (karma_old[0] + karma[0], karma_old[1] + karma[1])

    return ret


def user_vote_change_links(period=None, user=None):
    rel = Vote.rel(Account, Link)
    type = tdb.rel_types_id[rel._type_id]
    # rt = rel table
    # dt = data table
    rt, account_tt, link_tt, dt = type.rel_table

    aliases = tdb.alias_generator()
    author_dt = dt.alias(aliases.next())

    link_dt = tdb.types_id[Link._type_id].data_table[0].alias(aliases.next())

    # Create an SQL CASE statement for the subreddit vote multiplier
    cases = []
    for subreddit in subreddits_with_custom_karma_multiplier():
        cases.append( (sa.cast(link_dt.c.value,sa.Integer) == subreddit._id,
                      subreddit.post_karma_multiplier) )
    cases.append( (True, g.post_karma_multiplier) )       # The default article multiplier
    weight_cases = sa.case(cases)

    amount = sa.cast(rt.c.name, sa.Integer)
    cols = [
        author_dt.c.value,
        sa.func.sum(sa.case([(amount > 0, amount * weight_cases)], else_=0)),
        sa.func.sum(sa.case([(amount < 0, amount * -1 * weight_cases)], else_=0)),
    ]

    query = sa.and_(author_dt.c.thing_id == rt.c.rel_id,
                    author_dt.c.key == 'author_id',
                    link_tt.c.thing_id == rt.c.thing2_id,
                    link_dt.c.key == 'sr_id',
                    link_dt.c.thing_id == rt.c.thing2_id)
    if period is not None:
        earliest = datetime.now(g.tz) - timedelta(0, period)
        query.clauses.extend((rt.c.date >= earliest, link_tt.c.date >= earliest))
    if user is not None:
        query.clauses.append(author_dt.c.value == str(user._id))

    s = sa.select(cols, query, group_by=author_dt.c.value)

    rows = s.execute().fetchall()
    return [(int(r[0]), (r[1], r[2])) for r in rows]


def user_vote_change_comments(period=None, user=None):
    rel = Vote.rel(Account, Comment)
    type = tdb.rel_types_id[rel._type_id]
    # rt = rel table
    # dt = data table
    rt, account_tt, comment_tt, dt = type.rel_table

    aliases = tdb.alias_generator()
    author_dt = dt.alias(aliases.next())

    amount = sa.cast(rt.c.name, sa.Integer)
    cols = [
        author_dt.c.value,
        sa.func.sum(sa.case([(amount > 0, amount)], else_=0)),
        sa.func.sum(sa.case([(amount < 0, amount * -1)], else_=0)),
    ]

    query = sa.and_(author_dt.c.thing_id == rt.c.rel_id,
                    author_dt.c.key == 'author_id',
                    comment_tt.c.thing_id == rt.c.thing2_id)
    if period is not None:
        earliest = datetime.now(g.tz) - timedelta(0, period)
        query.clauses.extend((rt.c.date >= earliest, comment_tt.c.date >= earliest))
    if user is not None:
        query.clauses.append(author_dt.c.value == str(user._id))

    s = sa.select(cols, query, group_by=author_dt.c.value)

    rows = s.execute().fetchall()
    return [(int(r[0]), (r[1], r[2])) for r in rows]


def user_karma_adjustments(period=None, user=None):
    acct_info = tdb.types_id[Account._type_id]
    acct_thing, acct_data = acct_info.thing_table, acct_info.data_table[0]
    adj_info = tdb.types_id[KarmaAdjustment._type_id]
    adj_thing, adj_data = adj_info.thing_table, adj_info.data_table[0]

    aliases = tdb.alias_generator()
    adj_data_2 = adj_data.alias(aliases.next())

    amount = sa.cast(adj_data_2.c.value, sa.Integer)
    cols = [
        adj_data.c.value,
        sa.func.sum(sa.case([(amount > 0, amount)], else_=0)),
        sa.func.sum(sa.case([(amount < 0, amount * -1)], else_=0)),
    ]

    query = sa.and_(adj_data.c.thing_id == adj_thing.c.thing_id,
                    adj_data.c.key == 'account_id',
                    adj_data.c.thing_id == adj_data_2.c.thing_id,
                    adj_data_2.c.key == 'amount')
    if period is not None:
        earliest = datetime.now(g.tz) - timedelta(0, period)
        query.clauses.append(adj_thing.c.date >= earliest)
    if user is not None:
        query.clauses.append(adj_data.c.value == str(user._id))

    s = sa.select(cols, query, group_by=adj_data.c.value)

    rows = s.execute().fetchall()
    return [(int(r[0]), (r[1], r[2])) for r in rows]


def cache_key_user_karma(user, period):
    return 'account_{0}_karma_past_{1}_v2'.format(user._id, period)


def cached_monthly_user_change(user):
    key = cache_key_user_karma(user, SECONDS_PER_MONTH)
    ret = cache.get(key)
    if ret is not None:
        return ret

    ret = all_user_change(period=SECONDS_PER_MONTH, user=user)[user._id]
    cache.set(key, ret, CACHE_EXPIRY)
    return ret


def expire_user_change(user):
    cache.delete(cache_key_user_karma(user, SECONDS_PER_MONTH))


def cached_monthly_top_users():
    key = 'top_{0}_account_monthly_karma_v2'.format(NUM_TOP_USERS)
    ret = cache.get(key)
    if ret is not None:
        return ret

    start_time = time.time()
    ret = list(all_user_change(period=SECONDS_PER_MONTH).iteritems())
    ret.sort(key=lambda pair: -(pair[1][0] - pair[1][1]))  # karma, highest to lowest
    ret = ret[0:NUM_TOP_USERS]
    cache.set(key, ret, CACHE_EXPIRY)
    g.log.info("Calculate monthly_top_users took : %.2fs"%(time.time()-start_time))
    return ret
