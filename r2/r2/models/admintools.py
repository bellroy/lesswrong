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
from r2.lib.utils import tup

class AdminTools(object):
	"""Provides utility methods related to site admin tasks.  

	Note: many methods are currently dummy methods that pass or return a fixed value regardless of their inputs.
	"""
    def spam(self, thing, amount = 1, mark_as_spam = True, **kw):
	"""Mark each item in thing as spam if amount is greater than 0 else mark them as not spam"""
        things = tup(thing)
        for t in things:
            if mark_as_spam:
                t._spam = (amount > 0)
                t._commit()

    def report(self, thing, amount = 1):
        pass

    def ban_info(self, thing):
	"""Return and empty dictionary."""
        return {}

    def get_corrections(self, cls, min_date = None, max_date = None, limit = 50):
	"""Return an empty list."""
        return []

admintools = AdminTools()

def is_banned_IP(ip):
	"""Return False"""
    return False

def is_banned_domain(dom):
	"""Return False"""
    return False

def valid_thing(v, karma):
	"""Return True"""
    return True

def valid_user(v, sr, karma):
	"""Return True"""
    return True

def update_score(obj, up_change, down_change, new_valid_thing, old_valid_thing):
	"""Incremts obj's _ups by up_change and its _downs by down_change"""
     obj._incr('_ups',   up_change)
     obj._incr('_downs', down_change)

def compute_votes(wrapper, item):
	"""Sets wrapper's upvotes and downvotes to mach item's _ups and _downs."""
    wrapper.upvotes   = item._ups
    wrapper.downvotes = item._downs


try:
    from r2admin.models.admintools import *
except:
    pass


