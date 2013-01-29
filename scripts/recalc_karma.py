#!/usr/bin/env python

"""
A script for a one-time migration, from keeping track of karma in terms of
totals, to keeping track of up- and down-votes independently. It stores a SQLite
database with its progress in the current directory (independent from the actual
site database), and can be killed anytime and will resume its progress from
where it left off.
"""


from collections import namedtuple
from datetime import datetime
import os

import sqlalchemy as sa

from r2.lib.db import tdb_sql
from r2.models import Account, Comment, KarmaAdjustment, Link, Subreddit, Vote


########################### DATABASE ###################################

HERE = os.getcwd()  #os.path.dirname(__file__)
TEMP_DB_FILE = os.path.join(HERE, 'karma.db')

Kind = namedtuple('Kind', 'id desc')
kind_ids = {1: Kind(1, 'link'), 2: Kind(2, 'comment'), 3: Kind(3, 'adjustment')}
kinds = dict((k.desc, k) for k in kind_ids.values())

metadata = sa.MetaData()
kvstore = sa.Table('kvstore', metadata,
    sa.Column('id',         sa.Integer, primary_key=True),
    sa.Column('name',       sa.VARCHAR(255), nullable=False, unique=True),
    sa.Column('value',      sa.VARCHAR(255), nullable=False),
)
karmatotals = sa.Table('karmatotals', metadata,
    sa.Column('id',         sa.Integer, primary_key=True),
    sa.Column('account_id', sa.Integer, nullable=False),
    sa.Column('sr_id',      sa.Integer, nullable=False),
    sa.Column('kind',       sa.Integer, nullable=False),
    sa.Column('direction',  sa.BOOLEAN, nullable=False),
    sa.Column('amount',     sa.Integer, nullable=False),
)
sa.Index('idx_kt_acct_sr_kind_dir',
    karmatotals.c.account_id, karmatotals.c.sr_id,
    karmatotals.c.kind, karmatotals.c.direction,
    unique=True)


############################### CODE #################################

def main():
    KarmaCalc().run()


class KarmaCalc(object):
    def __init__(self):
        self.state = MigrateState()
        self.subreds_by_id = {}

    def run(self):
        self.read_votes(Link, 'link', 'vote_link')
        self.read_votes(Comment, 'comment', 'vote_comment')
        self.migrate_scan_adjustments()
        self.state.commit()

        self.write_karmas()
        self.state.commit()

        print('Terminus with success!')

    def migrate_scan_adjustments(self):
        # These should hopefully all fit in memory at once because this feature
        # is relatively new, but dividing up the work is still necessary in
        # order to run this script more than once.

        STEP = 100
        max_id = self.max_thing_id(KarmaAdjustment)
        id_start = int(self.state.kvstore.get('karmaadjustment.cur_read_id', '0'))

        print('Scanning {0}. Max id is {1}, starting at {2}'.format(
            'adjustments', max_id, id_start))

        for id_low in xrange(id_start, max_id + 1, STEP):
            adjs = list(KarmaAdjustment._query(
                KarmaAdjustment.c._id >= id_low,
                KarmaAdjustment.c._id < id_low + STEP, data=True))
            print('{0}: {1}, {2} of {3}'.format(
                datetime.now().isoformat(' '), 'adjustments', id_low, max_id))

            for adj in adjs:
                # adj.amount can be either positive or negative
                self.state.tally_karma(adj.account_id, adj.sr_id, 'adjustment', adj.amount)

            if adjs:
                max_id = max(a._id for a in adjs)
                self.state.kvstore['karmaadjustment.cur_read_id'] = str(max_id + 1)
                self.state.commit()

    def read_votes(self, cls2, karma_kind, kv_namespace):
        STEP = 100
        rel = Vote.rel(Account, cls2)
        max_id = self.max_rel_type_id(rel)
        id_start = int(self.state.kvstore.get(kv_namespace + '.cur_read_id', '0'))

        print('Scanning {0}. Highest vote id is {1}; starting at {2}'.format(
            rel._type_name, max_id, id_start))

        for id_low in xrange(id_start, max_id + 1, STEP):
            votes = list(self.query_rel_id_range(rel, id_low, id_low + STEP))
            print('{0}: {1}, {2} of {3}'.format(
                datetime.now().isoformat(' '), rel._type_name, id_low, max_id))

            for vote in votes:
                thing = cls2._byID(vote._thing2_id, data=True)
                amt = int(vote._name)  # can be either positive or negative
                self.state.tally_karma(thing.author_id, thing.sr_id, karma_kind, amt)

            if votes:
                max_id = max(v._id for v in votes)
                self.state.kvstore[kv_namespace + '.cur_read_id'] = str(max_id + 1)
                self.state.commit()

        print('Done with {0}!'.format(rel._type_name))

    def query_rel_id_range(self, rel, id_low, id_high):
        return rel._query(rel.c._rel_id >= id_low, rel.c._rel_id < id_high,
                          eager_load=True)

    def max_thing_id(self, thing_type):
        thing_type = tdb_sql.types_id[thing_type._type_id]
        thing_tbl = thing_type.thing_table
        return sa.select([sa.func.max(thing_tbl.c.thing_id)]).execute().scalar()

    def max_rel_type_id(self, rel_thing):
        thing_type = tdb_sql.rel_types_id[rel_thing._type_id]
        thing_tbl = thing_type.rel_table[0]
        return sa.select([sa.func.max(thing_tbl.c.rel_id)]).execute().scalar()


    def write_karmas(self):
        STEP = 100
        account_id_max = sa.select([sa.func.max(karmatotals.c.account_id)]).scalar()
        account_id_start = 0  #int(self.state.kvstore.get('karma.cur_write_account_id', '0'))

        print('Writing karma keys, starting at account {0}, max account id is {1}'.format(
            account_id_start, account_id_max))

        for account_id_low in xrange(account_id_start, account_id_max + 1, STEP):
            accounts = list(Account._query(
                Account.c._id >= account_id_low,
                Account.c._id < account_id_low + STEP))
            accounts = dict((a._id, a) for a in accounts)
            karmas = karmatotals.select(
                sa.and_(karmatotals.c.account_id >= account_id_low,
                        karmatotals.c.account_id < account_id_low + STEP)).execute().fetchall()

            print('{0}: writing karmas, {1} of {2} accounts'.format(
                datetime.now().isoformat(' '), account_id_low, account_id_max))

            for k in karmas:
                account = accounts.get(k['account_id'])
                if account is not None:
                    key = self.make_karma_key(k)
                    setattr(account, key, k['amount'])

            for ac in accounts.values():
                ac._commit()
            #self.state.kvstore['karma.cur_write_account_id'] = str(account_id_low + STEP)
            #self.state.commit()

    def get_sr_by_id(self, sr_id):
        sr = self.subreds_by_id.get(sr_id)
        if sr is None:
            sr = self.subreds_by_id[sr_id] = Subreddit._byID(sr_id, data=True)
        return sr

    def make_karma_key(self, karma):
        return 'karma_{0}_{1}_{2}'.format(
            ('downs', 'ups')[karma['direction']],
            kind_ids[karma['kind']].desc,
            self.get_sr_by_id(karma.sr_id).name)


class MigrateState(object):
    def __init__(self):
        metadata.bind = sa.create_engine('sqlite:///' + TEMP_DB_FILE).connect()
        self.bind = metadata.bind
        metadata.create_all()
        names_values = [kvstore.c.name, kvstore.c.value]
        self.kvstore = dict(self.bind.execute(sa.select(names_values)).fetchall())

        self.trans = self.bind.begin()

    def tally_karma(self, account_id, sr_id, kind, amount):
        # The total which is increased will be 'ups' if amount > 0, otherwise 'downs'
        upsert(self.bind, karmatotals, {
            'account_id': account_id,
            'sr_id': sr_id,
            'kind': kinds[kind].id,
            'direction': amount >= 0,
        }, {
            'amount': karmatotals.c.amount + abs(amount),
        }, {
            'amount': abs(amount),
        })

    def commit(self):
        for k, v in self.kvstore.iteritems():
            upsert(self.bind, kvstore, {'name': k}, {'value': v})
        self.trans.commit()
        self.trans = self.bind.begin()


def upsert(bind, table, pivots, values_update, values_insert=None):
    where = sa.and_(*[table.columns[k] == v for k, v in pivots.items()])
    row = bind.execute(table.select(where)).fetchone()
    if row:
        where = sa.and_(*[c == row[c] for c in table.primary_key])
        bind.execute(table.update(where, values_update))
    else:
        if values_insert is None:
            values_insert = values_update
        values_insert.update(pivots)
        bind.execute(table.insert(values_insert))


main()
