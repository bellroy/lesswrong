from r2.lib.db.thing import Thing

import pytz
from datetime import datetime
from r2.lib.utils import FixedOffset

class Meetup(Thing):
  def datetime(self):
    utc_timestamp = datetime.fromtimestamp(self.timestamp, pytz.timezone('utc'))
    tz = FixedOffset(self.tzoffset, None)
    return utc_timestamp.astimezone( tz )
