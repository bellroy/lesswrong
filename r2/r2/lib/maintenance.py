# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################

"""Routines for displaying maintenance messages"""

import pytz
import calendar
from datetime import datetime
import r2.lib.utils as utils
from pylons import g

MAINTENANCE_KEY = 'maintenance_scheduled_at'

def active():
  sched = scheduled_at()
  return sched and (datetime.now(pytz.utc) >= sched)

def scheduled():
  return scheduled_at is not None

def scheduled_at():
  scheduled_timestamp = g.permacache.get(MAINTENANCE_KEY)
  if scheduled_timestamp is not None:
    try:
        return datetime.fromtimestamp(scheduled_timestamp, pytz.utc)
    except ValueError:
        return None

  return None

def schedule_at(date_time):
  timestamp = calendar.timegm(date_time.utctimetuple())
  g.permacache.set(MAINTENANCE_KEY, timestamp)

def timeuntil():
  time = scheduled_at()
  return utils.timeuntil(time, resultion = 2) if time is not None else ""

def humantime():
  time = scheduled_at()
  return time.strftime('%H:%M %Z') if time is not None else ""
