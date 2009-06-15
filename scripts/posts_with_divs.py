import sys
import sqlalchemy as sa
from r2.lib.db import tdb_sql as tdb
from r2.models import Link
from r2.lib.db.thing import NotFound

def max_link_id():
    thing_type = tdb.types_id[Link._type_id]
    thing_tbl = thing_type.thing_table

    q = sa.select([sa.func.count(thing_tbl.c.thing_id)],
        thing_tbl.c.deleted == False
    )

    rows = q.execute().fetchall()
    return rows[0][0]

def posts_with_divs():
    link_count = max_link_id()
    print >>sys.stderr, "# %d links to process" % link_count
    for link_id in xrange(link_count):
        try:
            link = Link._byID(link_id, data=True)
        except NotFound:
            continue
    
        if hasattr(link, 'ob_permalink'):
            article = link.article
            if isinstance(article, str):
                try:
                    article = article.decode('utf-8')
                except UnicodeDecodeError:
                    print >>sys.stderr, "UnicodeDecodeError, using 'ignore' error mode, link: %d" % link._id
                    article = article.decode('utf-8', errors='ignore')
                
            if '<div' in article:
                print >>sys.stderr, link.canonocal_url.encode('utf-8')
