from r2.lib.db.thing import Thing

import pytz
import time
from datetime import datetime
from r2.lib.utils import FixedOffset
from r2.lib.db.operators import desc
from geolocator import gislib

class Meetup(Thing):
  def datetime(self):
    utc_timestamp = datetime.fromtimestamp(self.timestamp, pytz.utc)
    tz = FixedOffset(self.tzoffset, None)
    return utc_timestamp.astimezone(tz)

  @classmethod
  def add_props(cls, user, items):
    pass

  @classmethod
  def upcoming_meetups_query(cls):
    return Meetup._query(Meetup.c.timestamp > time.time(), data=True)

  @classmethod
  def upcoming_meetups_near(cls, location, max_distance, count = 5):
    query = cls.upcoming_meetups_query()
    query._limit = count
    meetups = list(query)

    # Find nearby ones
    if location:
        meetups = filter(lambda m: m.distance_to(point) <= max_distance, meetups)
    else:
        meetups.sort(key=lambda m: m.timestamp)

    return meetups


  def distance_to(self, location):
    """
    Returns the distance from this meetup to the passed point. The point is
    tuple, (lat, lng)
    """
    return gislib.getDistance((self.latitude, self.longitude), location)

  def keep_item(self, item):
    return True

  @staticmethod
  def cache_key(item):
    return False
