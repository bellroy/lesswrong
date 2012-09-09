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
from urllib import unquote_plus, quote_plus, urlopen, urlencode
from urlparse import urlparse, urlunparse
from threading import local, Thread
import Queue
from copy import deepcopy
import cPickle as pickle
import re, datetime, math, random, string, os, yaml

from datetime import datetime, timedelta, tzinfo
from pylons.i18n import ungettext, _
from r2.lib.filters import _force_unicode
from mako.filters import url_escape, url_unescape
from pylons import g        

iters = (list, tuple, set)

def tup(item, ret_is_single=False):
    """Forces casting of item to a tuple (for a list) or generates a
    single element tuple (for anything else)"""
    #return true for iterables, except for strings, which is what we want
    if hasattr(item, '__iter__'):
        return (item, False) if ret_is_single else item
    else:
        return ((item,), True) if ret_is_single else (item,)

def randstr(len, reallyrandom = False):
    """If reallyrandom = False, generates a random alphanumeric string
    (base-36 compatible) of length len.  If reallyrandom, add
    uppercase and punctuation (which we'll call 'base-93' for the sake
    of argument) and suitable for use as salt."""
    alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if reallyrandom:
        alphabet += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&\()*+,-./:;<=>?@[\\]^_{|}~'
    return ''.join(random.choice(alphabet)
                   for i in range(len))


class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'
    
    """
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value): 
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'

storage = Storage

def storify(mapping, *requireds, **defaults):
    """
    Creates a `storage` object from dictionary `mapping`, raising `KeyError` if
    d doesn't have all of the keys in `requireds` and using the default 
    values for keys found in `defaults`.

    For example, `storify({'a':1, 'c':3}, b=2, c=0)` will return the equivalent of
    `storage({'a':1, 'b':2, 'c':3})`.
    
    If a `storify` value is a list (e.g. multiple values in a form submission), 
    `storify` returns the last element of the list, unless the key appears in 
    `defaults` as a list. Thus:
    
        >>> storify({'a':[1, 2]}).a
        2
        >>> storify({'a':[1, 2]}, a=[]).a
        [1, 2]
        >>> storify({'a':1}, a=[]).a
        [1]
        >>> storify({}, a=[]).a
        []
    
    Similarly, if the value has a `value` attribute, `storify will return _its_
    value, unless the key appears in `defaults` as a dictionary.
    
        >>> storify({'a':storage(value=1)}).a
        1
        >>> storify({'a':storage(value=1)}, a={}).a
        <Storage {'value': 1}>
        >>> storify({}, a={}).a
        {}
    
    """
    def getvalue(x):
        if hasattr(x, 'value'):
            return x.value
        else:
            return x
    
    stor = Storage()
    for key in requireds + tuple(mapping.keys()):
        value = mapping[key]
        if isinstance(value, list):
            if isinstance(defaults.get(key), list):
                value = [getvalue(x) for x in value]
            else:
                value = value[-1]
        if not isinstance(defaults.get(key), dict):
            value = getvalue(value)
        if isinstance(defaults.get(key), list) and not isinstance(value, list):
            value = [value]
        setattr(stor, key, value)

    for (key, value) in defaults.iteritems():
        result = value
        if hasattr(stor, key): 
            result = stor[key]
        if value == () and not isinstance(result, tuple): 
            result = (result,)
        setattr(stor, key, result)
    
    return stor

def _strips(direction, text, remove):
    if direction == 'l': 
        if text.startswith(remove): 
            return text[len(remove):]
    elif direction == 'r':
        if text.endswith(remove):   
            return text[:-len(remove)]
    else: 
        raise ValueError, "Direction needs to be r or l."
    return text

def rstrips(text, remove):
    """
    removes the string `remove` from the right of `text`

        >>> rstrips("foobar", "bar")
        'foo'
    
    """
    return _strips('r', text, remove)

def lstrips(text, remove):
    """
    removes the string `remove` from the left of `text`
    
        >>> lstrips("foobar", "foo")
        'bar'
    
    """
    return _strips('l', text, remove)

def strips(text, remove):
    """removes the string `remove` from the both sides of `text`

        >>> strips("foobarfoo", "foo")
        'bar'
    
    """
    return rstrips(lstrips(text, remove), remove)

class Results():
    def __init__(self, sa_ResultProxy, build_fn, do_batch=False):
        self.rp = sa_ResultProxy
        self.fn = build_fn
        self.do_batch = do_batch

    @property
    def rowcount(self):
        return self.rp.rowcount

    def _fetch(self, res):
        if self.do_batch:
            return self.fn(res)
        else:
            return [self.fn(row) for row in res]

    def fetchall(self):
        return self._fetch(self.rp.fetchall())

    def fetchmany(self, n):
        rows = self._fetch(self.rp.fetchmany(n))
        if rows:
            return rows
        else:
            raise StopIteration

    def fetchone(self):
        row = self.rp.fetchone()
        if row:
            if self.do_batch:
                row = tup(row)
                return self.fn(row)[0]
            else:
                return self.fn(row)
        else:
            raise StopIteration

def string2js(s):
    """adapted from http://svn.red-bean.com/bob/simplejson/trunk/simplejson/encoder.py"""
    ESCAPE = re.compile(r'[\x00-\x19\\"\b\f\n\r\t]')
    ESCAPE_ASCII = re.compile(r'([\\"/]|[^\ -~])')
    ESCAPE_DCT = {
        # escape all forward slashes to prevent </script> attack
        '/': '\\/',
        '\\': '\\\\',
        '"': '\\"',
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
    }
    for i in range(20):
        ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))

    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'

r_base_url = re.compile("(?i)(?:.+?://)?(?:www[\d]*\.)?([^#]*[^#/])/?")
def base_url(url):
    res = r_base_url.findall(url)
    return (res and res[0]) or url

r_domain = re.compile("(?i)(?:.+?://)?(?:www[\d]*\.)?([^/:#?]*)")
def domain(s):
    """
        Takes a URL and returns the domain part, minus www., if
        present
    """
    res = r_domain.findall(s)
    domain = (res and res[0]) or s
    return domain.lower()

r_path_component = re.compile(".*?/(.*)")
def path_component(s):
    """
        takes a url http://www.foo.com/i/like/cheese and returns
        i/like/cheese
    """
    res = r_path_component.findall(base_url(s))
    return (res and res[0]) or s

r_title = re.compile('<title>(.*?)<\/title>', re.I|re.S)
r_charset = re.compile("<meta.*charset\W*=\W*([\w_-]+)", re.I|re.S)
r_encoding = re.compile("<?xml.*encoding=\W*([\w_-]+)", re.I|re.S)
def get_title(url):
    """Fetches the contents of url and extracts (and utf-8 encodes)
    the contents of <title>"""
    import chardet
    if not url or not url.startswith('http://'): return None
    try:
        content = urlopen(url).read()
        t = r_title.findall(content)
        if t:
            title = t[0].strip()
            en = (r_charset.findall(content) or
                  r_encoding.findall(content))
            encoding = en[0] if en else chardet.detect(content)["encoding"]
            if encoding:
                title = unicode(title, encoding).encode("utf-8")
            return title
    except: return None
       
valid_schemes = ('http', 'https', 'ftp', 'mailto')         
def sanitize_url(url, require_scheme = False):
    """Validates that the url is of the form

    scheme://domain/path/to/content#anchor?cruft

    using the python built-in urlparse.  If the url fails to validate,
    returns None.  If no scheme is provided and 'require_scheme =
    False' is set, the url is returned with scheme 'http', provided it
    otherwise validates"""
    if not url or ' ' in url:
        return

    url = url.strip()
    if url.lower() == 'self':
        return url

    u = urlparse(url)
    # first pass: make sure a scheme has been specified
    if not require_scheme and not u.scheme:
        url = 'http://' + url
        u = urlparse(url)

    if (u.scheme and u.scheme in valid_schemes
        and u.hostname and len(u.hostname) < 255
        and '%' not in u.netloc):
        return url

def timeago(interval):
    """Returns a datetime object corresponding to time 'interval' in
    the past.  Interval is of the same form as is returned by
    timetext(), i.e., '10 seconds'.  The interval must be passed in in
    English (i.e., untranslated) and the format is

    [num] second|minute|hour|day|week|month|year(s)
    """
    from pylons import g
    return datetime.now(g.tz) - timeinterval_fromstr(interval)

def timefromnow(interval):
    "The opposite of timeago"
    from pylons import g
    return datetime.now(g.tz) + timeinterval_fromstr(interval)
    
def timeinterval_fromstr(interval):
    "Used by timeago and timefromnow to generate timedeltas from friendly text"
    parts = interval.strip().split(' ')
    if len(parts) == 1:
        num = 1
        period = parts[0]
    elif len(parts) == 2:
        num, period = parts
        num = int(num)
    else:
        raise ValueError, 'format should be ([num] second|minute|etc)'
    period = rstrips(period, 's')

    d = dict(second = 1,
             minute = 60,
             hour   = 60 * 60,
             day    = 60 * 60 * 24,
             week   = 60 * 60 * 24 * 7,
             month  = 60 * 60 * 24 * 30,
             year   = 60 * 60 * 24 * 365)[period]
    delta = num * d
    return timedelta(0, delta)

def timetext(delta, resultion = 1, bare=True):
    """
    Takes a datetime object, returns the time between then and now
    as a nicely formatted string, e.g "10 minutes"
    Adapted from django which was adapted from
    http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n)),
      (1, lambda n: ungettext('second', 'seconds', n))
    )
    delta = max(delta, timedelta(0))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    for i, (seconds, name) in enumerate(chunks):
        count = math.floor(since / seconds)
        if count != 0:
            break

    from r2.lib.strings import strings
    if count == 0 and delta.seconds == 0 and delta != timedelta(0):
        n = math.floor(delta.microseconds / 1000)
        s = strings.number_label % (n, ungettext("millisecond", 
                                                 "milliseconds", n))
    else:
        s = strings.number_label % (count, name(int(count)))
        if resultion > 1:
            if i + 1 < len(chunks):
                # Now get the second item
                seconds2, name2 = chunks[i + 1]
                count2 = (since - (seconds * count)) / seconds2
                if count2 != 0:
                    s += ', %d %s' % (count2, name2(count2))
    if not bare: s += ' ' + _('ago')
    return s

def timesince(d, resultion = 1, bare = True):
    from pylons import g
    return timetext(datetime.now(g.tz) - d)

def timeuntil(d, resultion = 1, bare = True):
    from pylons import g
    return timetext(d - datetime.now(g.tz))

def epochtime(date):
    if not date:
        return "0"
    date = date.astimezone(g.tz)
    return date.strftime("%s")

def prettytime(date, seconds = False):
    date = date.astimezone(g.tz)
    return date.strftime('%d %B %Y %I:%M:%S%p' if seconds else '%d %B %Y %I:%M%p')

def rfc822format(date):
    return date.strftime('%a, %d %b %Y %H:%M:%S %z')

def usformat(date):
  """
  Format a datetime in US date format

  Makes the date readable by the Protoplasm datetime picker
  """
  return date.strftime('%m-%d-%Y %H:%M:%S')

def median(nums):
    """Find the median of a list of numbers, which is assumed to already be sorted."""
    count = len(nums)
    mid = count // 2
    if count % 2:
        return nums[mid]
    else:
        return (nums[mid - 1] + nums[mid]) / 2

def to_base(q, alphabet):
    if q < 0: raise ValueError, "must supply a positive integer"
    l = len(alphabet)
    converted = []
    while q != 0:
        q, r = divmod(q, l)
        converted.insert(0, alphabet[r])
    return "".join(converted) or '0'

def to36(q):
    return to_base(q, '0123456789abcdefghijklmnopqrstuvwxyz')

def query_string(dict):
    pairs = []
    for k,v in dict.iteritems():
        if v is not None:
            try:
                k = url_escape(unicode(k).encode('utf-8'))
                v = url_escape(unicode(v).encode('utf-8'))
                pairs.append(k + '=' + v)
            except UnicodeDecodeError:
                continue
    if pairs:
        return '?' + '&'.join(pairs)
    else:
        return ''

class UrlParser(object):
    """
    Wrapper for urlparse and urlunparse for making changes to urls.
    All attributes present on the tuple-like object returned by
    urlparse are present on this class, and are setable, with the
    exception of netloc, which is instead treated via a getter method
    as a concatenation of hostname and port.

    Unlike urlparse, this class allows the query parameters to be
    converted to a dictionary via the query_dict method (and
    correspondingly updated vi update_query).  The extension of the
    path can also be set and queried.

    The class also contains reddit-specific functions for setting,
    checking, and getting a path's subreddit.  It also can convert
    paths between in-frame and out of frame cname'd forms.

    """

    __slots__ = ['scheme', 'path', 'params', 'query',
                 'fragment', 'username', 'password', 'hostname',
                 'port', '_url_updates', '_orig_url', '_query_dict']

    valid_schemes = ('http', 'https', 'ftp', 'mailto')
    cname_get = "cnameframe"

    def __init__(self, url):
        u = urlparse(url)
        for s in self.__slots__:
            if hasattr(u, s):
                setattr(self, s, getattr(u, s))
        self._url_updates = {}
        self._orig_url    = url
        self._query_dict  = None

    def update_query(self, **updates):
        """
        Can be used instead of self.query_dict.update() to add/change
        query params in situations where the original contents are not
        required.
        """
        self._url_updates.update(updates)

    @property
    def query_dict(self):
        """
        Parses the `params' attribute of the original urlparse and
        generates a dictionary where both the keys and values have
        been url_unescape'd.  Any updates or changes to the resulting
        dict will be reflected in the updated query params
        """
        if self._query_dict is None:
            def _split(param):
                p = param.split('=')
                return (unquote_plus(p[0]),
                        unquote_plus('='.join(p[1:])))
            self._query_dict = dict(_split(p) for p in self.query.split('&')
                                    if p)
        return self._query_dict

    def path_extension(self):
        """
        Fetches the current extension of the path.
        """
        return self.path.split('/')[-1].split('.')[-1]

    def set_extension(self, extension):
        """
        Changes the extension of the path to the provided value (the
        "." should not be included in the extension as a "." is
        provided)
        """
        pieces = self.path.split('/')
        dirs = pieces[:-1]
        base = pieces[-1].split('.')
        base = '.'.join(base[:-1] if len(base) > 1 else base)
        if extension:
            base += '.' + extension
        dirs.append(base)
        self.path =  '/'.join(dirs)
        return self


    def unparse(self):
        """
        Converts the url back to a string, applying all updates made
        to the feilds thereof.

        Note: if a host name has been added and none was present
        before, will enforce scheme -> "http" unless otherwise
        specified.  Double-slashes are removed from the resultant
        path, and the query string is reconstructed only if the
        query_dict has been modified/updated.
        """
        # only parse the query params if there is an update dict
        q = self.query
        if self._url_updates or self._query_dict is not None:
            q = self._query_dict or self.query_dict
            q.update(self._url_updates)
            q = query_string(q).lstrip('?')

        # make sure the port is not doubly specified 
        if self.port and ":" in self.hostname:
            self.hostname = self.hostname.split(':')[0]

        # if there is a netloc, there had better be a scheme
        if self.netloc and not self.scheme:
            self.scheme = "http"
            
        return urlunparse((self.scheme, self.netloc,
                           self.path.replace('//', '/'),
                           self.params, q, self.fragment))

    def path_has_subreddit(self):
        """
        utility method for checking if the path starts with a
        subreddit specifier (namely /r/ or /categories/).
        """
        return (self.path.startswith('/r/') or
                self.path.startswith('/categories/'))

    def get_subreddit(self):
        """checks if the current url refers to a subreddit and returns
        that subreddit object.  The cases here are:
        
          * the hostname is unset or is g.domain, in which case it
            looks for /r/XXXX or /categories.  The default in this case
            is Default.
          * the hostname is a cname to a known subreddit.

        On failure to find a subreddit, returns None.
        """
        from pylons import g
        from r2.models import Subreddit, Sub, NotFound, Default
        try:
            if not self.hostname or self.hostname.startswith(g.domain):
                if self.path.startswith('/r/'):
                    return Subreddit._by_name(self.path.split('/')[2])
                elif self.path.startswith('/categories/'):
                    return Sub
                else:
                    return Default
            elif self.hostname:
                return Subreddit._by_domain(self.hostname)
        except NotFound:
            pass
        return None

    def is_reddit_url(self, subreddit = None):
        """utility method for seeing if the url is associated with
        reddit as we don't necessarily want to mangle non-reddit
        domains

        returns true only if hostname is nonexistant, a subdomain of
        g.domain, or a subdomain of the provided subreddit's cname.
        """
        from pylons import g
        return (not self.hostname or 
                self.hostname.endswith(g.domain) or
                (subreddit and subreddit.domain and
                 self.hostname.endswith(subreddit.domain)))

    def path_add_subreddit(self, subreddit):
        """ 
        Adds the subreddit's path to the path if another subreddit's
        prefix is not already present.
        """
        if not self.path_has_subreddit() and subreddit.path != '/categories/':
            self.path = (subreddit.path + self.path)
        return self

    @property
    def netloc(self):
        """
        Getter method which returns the hostname:port, or empty string
        if no hostname is present.
        """
        if not self.hostname:
            return ""
        elif self.port:
            return self.hostname + ":" + str(self.port)
        return self.hostname
    
    def mk_cname(self, require_frame = True, subreddit = None, port = None):
        """
        Converts a ?cnameframe url into the corresponding cnamed
        domain if applicable.  Useful for frame-busting on redirect.
        """

        # make sure the url is indeed in a frame
        if require_frame and not self.query_dict.has_key(self.cname_get):
            return self
        
        # fetch the subreddit and make sure it 
        subreddit = subreddit or self.get_subreddit()
        if subreddit and subreddit.domain:

            # no guarantee there was a scheme
            self.scheme = self.scheme or "http"

            # update the domain (preserving the port)
            self.hostname = subreddit.domain
            self.port = self.port or port

            # and remove any cnameframe GET parameters
            if self.query_dict.has_key(self.cname_get):
                del self._query_dict[self.cname_get]

            # remove the subreddit reference
            self.path = lstrips(self.path, subreddit.path)
            if not self.path.startswith('/'):
                self.path = '/' + self.path
        
        return self

    def is_in_frame(self):
        """
        Checks if the url is in a frame by determining if
        cls.cname_get is present.
        """
        return self.query_dict.has_key(self.cname_get)

    def put_in_frame(self):
        """
        Adds the cls.cname_get get parameter to the query string.
        """
        self.update_query(**{self.cname_get:random.random()})

    def __repr__(self):
        return "<URL %s>" % repr(self.unparse())


def to_js(content, callback="document.write", escape=True):
    before = after = ''
    if callback:
        before = callback + "("
        after = ");"
    if escape:
        content = string2js(content)
    return before + content + after

class TransSet(local):
    def __init__(self, items = ()):
        self.set = set(items)
        self.trans = False

    def begin(self):
        self.trans = True

    def add_engine(self, engine):
        if self.trans:
            return self.set.add(engine.begin())

    def clear(self):
        return self.set.clear()

    def __iter__(self):
        return self.set.__iter__()

    def commit(self):
        for t in self:
            t.commit()
        self.clear()

    def rollback(self):
        for t in self:
            t.rollback()
        self.clear()

    def __del__(self):
        self.commit()

def pload(fname, default = None):
    "Load a pickled object from a file"
    try:
        f = file(fname, 'r')
        d = pickle.load(f)
    except IOError:
        d = default
    else:
        f.close()
    return d

def psave(fname, d):
    "Save a pickled object into a file"
    f = file(fname, 'w')
    pickle.dump(d, f)
    f.close()

def unicode_safe(res):
    try:
        return str(res)
    except UnicodeEncodeError:
        return unicode(res).encode('utf-8')

def decompose_fullname(fullname):
    """
        decompose_fullname("t3_e4fa") ->
            (Thing, 3, 658918)
    """
    from r2.lib.db.thing import Thing,Relation
    if fullname[0] == 't':
        type_class = Thing
    elif fullname[0] == 'r':
        type_class = Relation

    type_id36, thing_id36 = fullname[1:].split('_')

    type_id = int(type_id36,36)
    id      = int(thing_id36,36)

    return (type_class, type_id, id)



class Worker:
    def __init__(self):
        self.q = Queue.Queue()
        self.t = Thread(target=self._handle)
        self.t.setDaemon(True)
        self.t.start()

    def _handle(self):
        while True:
            fn = self.q.get()
            try:
                fn()
            except:
                import traceback
                print traceback.format_exc()
                

    def do(self, fn):
        self.q.put(fn)

worker = Worker()

def asynchronous(func):
    def _asynchronous(*a, **kw):
        f = lambda: func(*a, **kw)
        worker.do(f)
    return _asynchronous
    
def cols(lst, ncols):
    """divides a list into columns, and returns the
    rows. e.g. cols('abcdef', 2) returns (('a', 'd'), ('b', 'e'), ('c',
    'f'))"""
    nrows = int(math.ceil(1.*len(lst) / ncols))
    lst = lst + [None for i in range(len(lst), nrows*ncols)]
    cols = [lst[i:i+nrows] for i in range(0, nrows*ncols, nrows)]
    rows = zip(*cols)
    rows = [filter(lambda x: x is not None, r) for r in rows]
    return rows

def fetch_things(t_class,since,until,batch_fn=None,
                 *query_params, **extra_query_dict):
    """
        Simple utility function to fetch all Things of class t_class
        (spam or not, but not deleted) that were created from 'since'
        to 'until'
    """

    from r2.lib.db.operators import asc

    if not batch_fn:
        batch_fn = lambda x: x

    query_params = ([t_class.c._date >= since,
                     t_class.c._date <  until,
                     t_class.c._spam == (True,False)]
                    + list(query_params))
    query_dict   = {'sort':  asc('_date'),
                    'limit': 100,
                    'data':  True}
    query_dict.update(extra_query_dict)

    q = t_class._query(*query_params,
                        **query_dict)
    
    orig_rules = deepcopy(q._rules)

    things = list(q)
    while things:
        things = batch_fn(things)
        for t in things:
            yield t
        q._rules = deepcopy(orig_rules)
        q._after(t)
        things = list(q)

def fetch_things2(query, chunk_size = 100, batch_fn = None):
    """Incrementally run query with a limit of chunk_size until there are
    no results left. batch_fn transforms the results for each chunk
    before returning."""
    orig_rules = deepcopy(query._rules)
    query._limit = chunk_size
    items = list(query)
    done = False
    while items and not done:
        #don't need to query again at the bottom if we didn't get enough
        if len(items) < chunk_size:
            done = True

        if batch_fn:
            items = batch_fn(items)

        for i in items:
            yield i

        if not done:
            query._rules = deepcopy(orig_rules)
            query._after(i)
            items = list(query)

def set_emptying_cache():
    """
        The default thread-local cache is a regular dictionary, which
        isn't designed for long-running processes. This sets the
        thread-local cache to be a SelfEmptyingCache, which naively
        empties itself out every N requests
    """
    from pylons import g
    from r2.lib.cache import SelfEmptyingCache
    g.cache.caches = [SelfEmptyingCache(),] + list(g.cache.caches[1:])

def find_recent_broken_things(from_time = None, delete = False):
    """
        Occasionally (usually during app-server crashes), Things will
        be partially written out to the database. Things missing data
        attributes break the contract for these things, which often
        breaks various pages. This function hunts for and destroys
        them as appropriate.
    """
    from r2.models import Link,Comment

    if not from_time:
        from_time = timeago("1 hour")

    to_time = timeago("60 seconds")

    for (cls,attrs) in ((Link,('author_id','sr_id')),
                        (Comment,('author_id','sr_id','body','link_id'))):
        find_broken_things(cls,attrs,
                           from_time, to_time,
                           delete=delete)

def find_broken_things(cls,attrs,from_time,to_time,delete = False):
    """
        Take a class and list of attributes, searching the database
        for Things of that class that are missing those attributes,
        deleting them if requested
    """
    for t in fetch_things(cls,from_time,to_time):
        for a in attrs:
            try:
                # try to retreive the attribute
                getattr(t,a)
            except AttributeError:
                # that failed; let's explicitly load it, and try again
                print "Reloading %s" % t._fullname
                t._load()
                try:
                    getattr(t,a)
                except AttributeError:
                    # it still broke. We should delete it
                    print "%s is missing '%s'" % (t._fullname,a)
                    if delete:
                        t._deleted = True
                        t._commit()
                    break

def timeit(func):
    "Run some function, and return (RunTimeInSeconds,Result)"
    before=time.time()
    res=func()
    return (time.time()-before,res)
def lineno():
    "Returns the current line number in our program."
    import inspect
    print "%s\t%s" % (datetime.now(),inspect.currentframe().f_back.f_lineno)

class IteratorChunker(object):
    def __init__(self,it):
        self.it = it
        self.done=False

    def next_chunk(self,size):
        chunk = []
        if not self.done:
            try:
                for i in xrange(size):
                    chunk.append(self.it.next())
            except StopIteration:
                self.done=True
        return chunk

def IteratorFilter(iterator, fn):
    for x in iterator:
        if fn(x):
            yield x

def UniqueIterator(iterator):
    """
    Takes an iterator and returns an iterator that returns only the
    first occurence of each entry
    """
    so_far = set()
    def no_dups(x):
        if x in so_far:
            return False
        else:
            so_far.add(x)
            return True

    return IteratorFilter(iterator, no_dups)

# def modhash(user, rand = None, test = False):
#     return user.name

# def valid_hash(user, hash):
#     return True

def check_cheating(loc):
    pass
        
def vote_hash(user, thing, note='valid'):
    return user.name

def valid_vote_hash(hash, user, thing):
    return True

def safe_eval_str(unsafe_str):
    return unsafe_str.replace('\\x3d', '=').replace('\\x26', '&')

rx_whitespace = re.compile('\s+', re.UNICODE)
rx_notsafe = re.compile('\W+', re.UNICODE)
rx_underscore = re.compile('_+', re.UNICODE)
def title_to_url(title, max_length = 50):
    """Takes a string and makes it suitable for use in URLs"""
    title = _force_unicode(title)           #make sure the title is unicode
    title = rx_whitespace.sub('_', title)   #remove whitespace
    title = rx_notsafe.sub('', title)       #remove non-printables
    title = rx_underscore.sub('_', title)   #remove double underscores
    title = title.strip('_')                #remove trailing underscores
    title = title.lower()                   #lowercase the title

    if len(title) > max_length:
        #truncate to nearest word
        title = title[:max_length]
        last_word = title.rfind('_')
        if (last_word > 0):
            title = title[:last_word]
    return title

def trace(fn):
    from pylons import g
    def new_fn(*a,**kw):
        ret = fn(*a,**kw)
        g.log.debug("Fn: %s; a=%s; kw=%s\nRet: %s"
                    % (fn,a,kw,ret))
        return ret
    return new_fn

def remote_addr(env):
  """
  Returns the remote address for the WSGI env passed

  Takes proxies into consideration
  """
  # In production the remote address is always the load balancer
  # So check X-Forwarded-For first
  # E.g. HTTP_X_FORWARDED_FOR: '66.249.72.73, 75.101.144.164'
  if env.has_key('HTTP_X_FORWARDED_FOR'):
    ips = re.split(r'\s*,\s*', env['HTTP_X_FORWARDED_FOR'])
    if len(ips) > 0:
      return ips[0]

  return env['REMOTE_ADDR']


# A class building tzinfo objects for a fixed offset.
class FixedOffset(tzinfo):
    """Fixed offset in hours east from UTC. name may be None"""
    def __init__(self, offset, name):
        self.offset = timedelta(hours = offset)
        self.name = name
        # tzinfo.__init__(self, name)

    def utcoffset(self, dt):
        return self.offset

    def tzname(self, dt):
        return self.name

    def dst(self, dt):
        return timedelta(0)

