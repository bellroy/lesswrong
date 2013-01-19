#!/usr/bin/env python

"""
A script to recalculate karma by scanning and summing all votes. It also
includes code for a one-time migration, from keeping track of karma in terms
of totals, to keeping track of up- and down-votes independently.
"""

from collections import defaultdict

from sqlalchemy import func, select

from r2.lib.db import tdb_sql
from r2.lib.db.thing import NotFound
from r2.models import Account, Comment, KarmaAdjustment, Link, Subreddit, Vote


def main():
    KarmaCalc(dry_run=False, migrate=True).run()


class KarmaCalc:
    def __init__(self, dry_run, migrate):
        self.dry_run = dry_run
        self.migrate = migrate
        self.new_values = defaultdict(lambda: defaultdict(int))

    def run(self):
        self.vote_scan(Link, 'link', get_sr_mult)
        self.vote_scan(Comment, 'comment', id_like_a_one)
        if self.migrate:
            self.migrate_scan_adjustments()

        self.report()
        if not self.dry_run:
            print('committing...')
            self.commit()

    def migrate_scan_adjustments(self):
        adjs = KarmaAdjustment._query(data=True)
        for adj in adjs:
            sr = Subreddit._byID(adj.sr_id, data=True)
            gravity = 'ups' if adj.amount >= 0 else 'downs'
            key = 'karma_{0}_adjustment_{1}'.format(gravity, sr.name)
            self.new_values[adj.account_id][key] += abs(adj.amount)

    def vote_scan(self, cls2, karma_kind, mult_func):
        rel = Vote.rel(Account, cls2)
        for vote in self.batch_query_rel_all(rel):
            thing = cls2._byID(vote._thing2_id, data=True)
            sr = thing.subreddit_slow
            mult = 1  #mult_func(thing)
            amt = int(vote._name)
            gravity = 'ups' if amt >= 0 else 'downs'
            key = 'karma_{0}_{1}_{2}'.format(gravity, karma_kind, sr.name)
            self.new_values[thing.author_id][key] += abs(amt * mult)

    def batch_query_rel_all(self, rel):
        max_id = self.max_rel_type_id(rel)
        for id_low in xrange(max_id + 1):
            try:
                yield rel._byID(id_low, data=True)
            except NotFound:
                pass  # must be deleted or somesuch

    def max_rel_type_id(self, rel_thing):
        thing_type = tdb_sql.rel_types_id[rel_thing._type_id]
        thing_tbl = thing_type.rel_table[0]
        rows = select([func.max(thing_tbl.c.rel_id)]).execute().fetchall()
        return rows[0][0]

    def commit(self):
        for account_id, pairs in self.new_values.iteritems():
            try:
                account = Account._byID(account_id, data=True)
            except NotFound:
                continue

            for k, v in pairs.iteritems():
                setattr(account, k, v)
            account._commit()

    def report(self):
        different = 0
        total = len(self.new_values)
        logged_keys = set()

        for account_id, pairs in self.new_values.iteritems():
            try:
                account = Account._byID(account_id, data=True)
            except NotFound:
                continue

            if self.migrate:
                for k, v in list(pairs.iteritems()):
                    _, dir, kind, sr = k.split('_')
                    old_total = getattr(account, '{0}_{1}_karma'.format(sr, kind), 0)
                    new_total = pairs['karma_ups_{0}_{1}'.format(kind, sr)] - \
                                pairs['karma_downs_{0}_{1}'.format(kind, sr)]
                    if old_total != new_total:
                        different += 1
                        if (account.name, kind, sr) not in logged_keys:
                            logged_keys.add((account.name, kind, sr))
                            print('{0}["{1}_{2}"] differs - old={3}, new={4}'.format(
                                account.name, kind, sr, old_total, new_total))
            else:
                for k, v in pairs.iteritems():
                    old_v = getattr(account, k, 0)
                    if v != old_v:
                        print('{0} differs - old={1}, new={2}'.format(k, old_v, v))

        print('{0} out of {1} values differed'.format(different, total))


def get_sr_mult(link):
    return link.subreddit_slow.post_karma_multiplier


def id_like_a_one(comment):
    return 1


main()
