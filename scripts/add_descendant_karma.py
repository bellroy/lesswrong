from r2.models.link import Comment, Link
import sqlalchemy as sa

from r2.lib.db import tdb_sql

def max_thing_id(thing_type):
    thing_type = tdb_sql.types_id[thing_type._type_id]
    thing_tbl = thing_type.thing_table
    return sa.select([sa.func.max(thing_tbl.c.thing_id)]).execute().scalar()

def run():

    STEP = 100
    thing = Link
    max_id = max_thing_id(thing)
    id_start = 0

    for id_low in xrange(id_start, max_id + 1, STEP):
        print "Add desc karma for links %s to %s" % (id_low, id_low + STEP)

        links = list(query_thing_id_range(thing, id_low, id_low + STEP))

        for link in links:
            if not link._loaded:
                link._load()
            comments = list(Comment._query(Comment.c.link_id == link._id, eager_load = True))
            link_descendant_karma = 0
            for comment in comments:
                if not comment._loaded:
                    comment._load()
                if hasattr(comment, 'parent_id') and comment.parent_id:
                    Comment._byID(comment.parent_id).incr_descendant_karma([], comment._ups - comment._downs)
                link_descendant_karma += (comment._ups - comment._downs)

            link._incr('_descendant_karma', link_descendant_karma)

def query_thing_id_range(thing, id_low, id_high):
    return thing._query(thing.c._id >= id_low, thing.c._id < id_high,
                      eager_load=True)

run()
