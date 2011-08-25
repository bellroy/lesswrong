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
import sqlalchemy as sa
from r2.models import Account, Vote, Link, Subreddit, Comment
from r2.lib.db import tdb_sql as tdb
from r2.lib import utils
import time

from pylons import g 
cache = g.cache

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

def top_users():
    type = tdb.types_id[Account._type_id]
    tt, dt = type.thing_table, type.data_table[0]

    aliases = tdb.alias_generator()
    karma = dt.alias(aliases.next())

    cases = [
        (karma.c.key.like('%_link_karma'),
            sa.cast(karma.c.value, sa.Integer) * g.post_karma_multiplier)
    ]

    for subreddit in subreddits_with_custom_karma_multiplier():
        key = "%s_link_karma" % subreddit.name
        cases.insert(0, (karma.c.key == key,
            sa.cast(karma.c.value, sa.Integer) * subreddit.post_karma_multiplier))

    s = sa.select(
        [tt.c.thing_id],
        sa.and_(tt.c.spam == False,
              tt.c.deleted == False,
              karma.c.thing_id == tt.c.thing_id,
              karma.c.key.like('%_karma')),
        group_by = [tt.c.thing_id],
        order_by = sa.desc(sa.func.sum(
            sa.case(cases, else_ = sa.cast(karma.c.value, sa.Integer))
        )),
        limit = 10)
    # Translation of query:
    # SELECT
    #  reddit_thing_account.thing_id
    # FROM
    #   reddit_thing_account,
    #   reddit_data_account
    # WHERE
    #  (reddit_thing_account.spam = 'f' AND
    #   reddit_thing_account.deleted = 'f' AND
    #   reddit_thing_account.thing_id = reddit_data_account.thing_id AND
    #   reddit_data_account.key LIKE '%_karma')
    # GROUP BY
    #   reddit_thing_account.thing_id
    # ORDER BY
    #  sum(
    #    CASE
    #      WHEN reddit_data_account.key = 'lesswrong_link_karma' THEN
    #        CAST(reddit_data_account.value AS INTEGER) * 10
    #      ELSE CAST(reddit_data_account.value AS INTEGER)
    #    END
    #  ) DESC
    # LIMIT 10
    rows = s.execute().fetchall()
    return [r.thing_id for r in rows]

# Calculate the karma change for the given period for all users
# TODO:  handle deleted users, spam articles and deleted articles, (and deleted comments?)
def all_user_change(period = '1 day'):
    res={}

    link_karma = user_vote_change_links(period)
    for name,val in link_karma:
        res[name]=val

    comment_karma = user_vote_change_comments(period)
    for name, val in comment_karma:
        res[name] = val + res.get(name,0)

    return res


def user_vote_change_links(period = '1 day'):
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


    date = utils.timeago(period)
    
    s = sa.select([author_dt.c.value, sa.func.sum(sa.cast(rt.c.name, sa.Integer) * sa.case(cases))],
                  sa.and_(rt.c.date >= date,
                          author_dt.c.thing_id == rt.c.rel_id,
                          author_dt.c.key == 'author_id',
                          link_tt.c.thing_id == rt.c.thing2_id,
                          link_tt.c.date >= date,
                          link_dt.c.key == 'sr_id',
                          link_dt.c.thing_id == rt.c.thing2_id),
                  group_by = author_dt.c.value)

    rows = s.execute().fetchall()
    return [(int(r.value), r.sum) for r in rows]

def user_vote_change_comments(period = '1 day'):
    rel = Vote.rel(Account, Comment)
    type = tdb.rel_types_id[rel._type_id]
    # rt = rel table
    # dt = data table
    rt, account_tt, comment_tt, dt = type.rel_table

    aliases = tdb.alias_generator()
    author_dt = dt.alias(aliases.next())

    date = utils.timeago(period)
    
    s = sa.select([author_dt.c.value, sa.func.sum(sa.cast(rt.c.name, sa.Integer))],
                  sa.and_(rt.c.date >= date,
                          author_dt.c.thing_id == rt.c.rel_id,
                          author_dt.c.key == 'author_id',
                          comment_tt.c.thing_id == rt.c.thing2_id,
                          comment_tt.c.date >= date),
                  group_by = author_dt.c.value)

    rows = s.execute().fetchall()

    return [(int(r.value), r.sum) for r in rows]

USER_CHANGE_CACHE_KEY = 'all_user_change'

def cached_all_user_change():
    r = cache.get(USER_CHANGE_CACHE_KEY)
    if not r:
        start_time = time.time()
        changes = all_user_change('30 days')
        s = sorted(changes.iteritems(), key=lambda x: x[1])
        s.reverse()
        r = [changes, s[0:5]]
        cache.set(USER_CHANGE_CACHE_KEY, r, 3600)
        g.log.info("Calculate all users karma change took : %.2fs"%(time.time()-start_time))
    return r

# def calc_stats():
#     top = top_users()
#     top_day = top_user_change('1 day')
#     top_week = top_user_change('1 week')
#     return (top, top_day, top_week)

# def set_stats():
#     cache.set('stats', calc_stats())
