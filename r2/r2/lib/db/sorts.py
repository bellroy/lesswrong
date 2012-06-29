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
from math import log, sqrt
from datetime import datetime, timedelta
from r2.config.databases import tz

epoch = datetime(1970, 1, 1, tzinfo = tz)

def epoch_seconds(date):
    """Returns the number of seconds from the epoch to date. Should match
    the number returned by the equivalent function in postgres."""
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)
    
def score(ups, downs):
    return ups - downs

def hot(ups, downs, date):
    """The hot formula. Should match the equivalent function in postgres."""
    s = score(ups, downs)
    order = log(max(abs(s), 1), 10)
    sign = 1 if s > 0 else -1 if s < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(order + sign * seconds / 45000, 7)

def controversy(ups, downs):
    """The controversy sort."""
    return float(ups + downs) / max(abs(score(ups, downs)), 1)


def _confidence(ups, downs):
    """The confidence sort.
       http://www.evanmiller.org/how-not-to-sort-by-average-rating.html"""
    n = ups + downs

    if n == 0:
        return 0

    z = 1.281551565545 # 80% confidence
    p = float(ups) / n

    left = p + 1/(2*n)*z*z
    right = z*sqrt(p*(1-p)/n + z*z/(4*n*n))
    under = 1+1/n*z*z

    return (left - right) / under

# precompute low values
up_range = 400
down_range = 100
_confidences = []
for _ups in xrange(up_range):
    for _downs in xrange(down_range):
        _confidences.append(_confidence(_ups, _downs))

def confidence(ups, downs):
    if ups + downs == 0:
        return 0
    elif ups < up_range and downs < down_range:  # check if pair is precomputed
        return _confidences[downs + ups * down_range]
    else:
        return _confidence(ups, downs)

