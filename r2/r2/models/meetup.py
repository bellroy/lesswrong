from r2.lib.db.thing import Thing

import pytz
import time
from datetime import datetime
from r2.lib.utils import FixedOffset
from r2.lib.db.operators import desc

class Meetup(Thing):
  def datetime(self):
    utc_timestamp = datetime.fromtimestamp(self.timestamp, pytz.utc)
    tz = FixedOffset(self.tzoffset, None)
    return utc_timestamp.astimezone(tz)

  @classmethod
  def add_props(cls, user, items):
    pass

  @classmethod
  def upcoming_meetups(cls):
    meetups = list(Meetup._query(Meetup.c.timestamp > time.time(), limit=5, data=True))

    # Sort in Python because the Thing API only provides sorting by base columns
    meetups.sort(key=lambda m: m.timestamp)
    return meetups

  def keep_item(self, item):
    return True

  @staticmethod
  def cache_key(item):
    return False
