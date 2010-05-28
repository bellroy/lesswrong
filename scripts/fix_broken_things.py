import r2.lib.utils as utils
from pylons import g
import datetime

def fix_all_broken_things(delete=False):
    from r2.models import Link,Comment

    # 2009-07-21 is the first broken thing at the time of writing.
    from_time = datetime.datetime(2009, 7, 21, tzinfo=g.tz)
    to_time   = utils.timeago('60 seconds')

    for (cls,attrs) in ((Link,('author_id','sr_id')),
                        (Comment,('author_id','sr_id','body','link_id'))):
        utils.find_broken_things(cls,attrs,
                                 from_time, to_time,
                                 delete=delete)

