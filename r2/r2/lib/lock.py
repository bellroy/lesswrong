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

from __future__ import with_statement
from threading import Lock
from time import sleep
from datetime import datetime
import sys
import threading

from pylons import c

class TimeoutExpired(Exception): pass

_LOG_LOCK = Lock()

class MemcacheLock(object):
    """A simple global lock based on the memcache 'add' command. We
    attempt to grab a lock by 'adding' the lock name. If the response
    is True, we have the lock. If it's False, someone else has it."""

    def __init__(self, key, cache, time = 30, timeout = 30):
        self.key = key
        self.cache = cache
        self.time = time
        self.timeout = timeout
        self.have_lock = False
        self.log('__init__')

    def __delitem__(self, key):
        self.log('__del__')

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, type, value, tb):
        self.release()

    def log(self, msg, *args):
        with _LOG_LOCK:
            print >>sys.stderr, datetime.utcnow().isoformat(' '), \
                '[MemcacheLock tid={0!r} id={1!r} key={2!r}]'.format(
                    threading.currentThread().ident, id(self), self.key), \
                msg.format(*args)
            sys.stderr.flush()

    def acquire(self):
        """
        Repeatedly try to acquire the lock, for `self.timeout` seconds, before
        giving up and raising an exception.
        """
        self.log('acquire enter')

        start = datetime.now()

        # try and fetch the lock, looping until it's available
        while not self.try_acquire():
            if (datetime.now() - start).seconds > self.timeout:
                raise TimeoutExpired
            sleep(0.1)

        self.log('acquire exit')

    def try_acquire(self):
        """
        Make one attempt to acquire the lock, and return immediately. Return
        `True` if we hold the lock upon returning from this method, and `False`
        if it's currently held elsewhere.
        """
        if not c.locks:
            c.locks = {}

        # if this thread already has this lock, move on
        if c.locks.get(self.key):
            return True

        # memcached will return true if the key was added, and false if it
        # already existed
        if not self.cache.add(self.key, 1, time = self.time):
            return False

        # tell this thread we have this lock so we can avoid deadlocks
        # of requests for the same lock in the same thread
        c.locks[self.key] = True
        self.have_lock = True
        return True

    def release(self):
        self.log('release enter')

        # only release the lock if we gained it in the first place
        if self.have_lock:
            self.cache.delete(self.key)
            del c.locks[self.key]

        self.log('release exit')


def make_lock_factory(cache):
    def factory(key):
        return MemcacheLock(key, cache)
    return factory
