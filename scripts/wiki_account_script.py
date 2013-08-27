from r2.models import Account, PendingJob

users = list(Account._query())
for user in users:
    if hasattr(user, 'email'):
        data = {'name' : user.name, 'password' : None, 'email' : user.email, 'attempt' : 0}
        PendingJob.store(None, 'create_wiki_account', data)

from r2.models.link import Comment, Link
import sqlalchemy as sa

from r2.lib.db import tdb_sql

def max_thing_id(thing_type):
    thing_type = tdb_sql.types_id[thing_type._type_id]
    thing_tbl = thing_type.thing_table
    return sa.select([sa.func.max(thing_tbl.c.thing_id)]).execute().scalar()

def run():

    STEP = 100
    thing = Account
    max_id = max_thing_id(thing)
    id_start = 0

    for id_low in xrange(id_start, max_id + 1, STEP):
        users = list(query_thing_id_range(thing, id_low, id_low + STEP))

        for user in users:
            if not user._loaded:
                user._load()
            if hasattr(user, 'email'):
                data = {'name' : user.name, 'password' : None, 'email' : user.email, 'attempt' : 0}
                PendingJob.store(None, 'create_wiki_account', data)

def query_thing_id_range(thing, id_low, id_high):
    return thing._query(thing.c._id >= id_low, thing.c._id < id_high,
                      eager_load=True)

run()
