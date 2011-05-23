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
    return Meetup._query(Meetup.c.timestamp > time.time(), limit=5, data=True)

  @classmethod
  def upcoming_meetups(cls):
    meetups = list(cls.upcoming_meetups_query())

    # Sort in Python because the Thing API only provides sorting by base columns
    meetups.sort(key=lambda m: m.timestamp)
    return meetups

  @classmethod
  def upcoming_meetups_near(cls, point):
    meetups = list(cls.upcoming_meetups_query())

    # Find nearby ones
    meetups = filter(lambda m: m.distance_to(point) < 100, meetups)

    # Sort in Python because the Thing API only provides sorting by base columns
    #meetups.sort(key=lambda m: )
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
