from r2.lib.db.thing import Thing

import time
from datetime import datetime
from r2.lib.utils import FixedOffset
from r2.lib.db.operators import desc
from geolocator import gislib
# must be here to stop bizarre NotImplementedErrors being raise in the datetime
# method below
import pytz
from r2.models.account import FakeAccount
from r2.models import Subreddit
from account import Account

from pylons import g
from geolocator.providers import MaxMindCityDataProvider

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
    """Return query for all meetups that are in the future"""
    # Warning, this timestamp inequality is actually done as a string comparison
    # in the db for some reason.  BUT, since epoch seconds won't get another digit
    # for another 275 years, we're good for now...
    return Meetup._query(Meetup.c.timestamp > time.time(), data=True, sort='_date')

  @classmethod
  def upcoming_meetups_by_timestamp(cls):
    """Return upcoming meetups ordered by soonest first"""
    # This doesn't do nice db level paginations, but there should only
    # be a smallish number of meetups
    query = cls.upcoming_meetups_query()
    meetups = list(query)
    meetups.sort(key=lambda m: m.timestamp)
    return map(lambda m: m._fullname, meetups)


  @classmethod
  def upcoming_meetups_near(cls, location, max_distance, count = 5):
    query = cls.upcoming_meetups_query()
    meetups = list(query)

    if not location:
      meetups.sort(key=lambda m: m.timestamp)
    else:
      if max_distance:
        # Only find nearby ones, sorted by time
        meetups = filter(lambda m: m.distance_to(location) <= max_distance, meetups)
        meetups.sort(key=lambda m: m.timestamp)
      else:
        # No max_distance, so just order by distance
        meetups.sort(key=lambda m: m.distance_to(location))

    return meetups[:count]

  def distance_to(self, location):
    """
    Returns the distance from this meetup to the passed point. The point is
    tuple, (lat, lng)
    """
    return gislib.getDistance((self.latitude, self.longitude), location)

  def keep_item(self, item):
    return True

  def can_edit(self, user, user_is_admin=False):
    """Returns true if the supplied user is allowed to edit this meetup"""
    if user is None or isinstance(user, FakeAccount):
      return False
    elif user_is_admin or self.author_id == user._id:
      return True
    elif Subreddit._by_name('discussion').is_editor(user):
      return True
    else:
      return False

  @staticmethod
  def cache_key(item):
    return False

  @staticmethod
  def group_cache_key():
    """ Used with CacheUtils.get_key_group_value """
    return "meetup-inc-key"

  def author(self):
    return Account._byID(self.author_id, True)

  @staticmethod
  def geoLocateIp(ip):
    geo = MaxMindCityDataProvider(g.geoip_db_path, "GEOIP_STANDARD")
    try:
      location = geo.getLocationByIp(ip)
    except TypeError:
      # geolocate can attempt to index into a None result from GeoIP
      location = None
    return location
