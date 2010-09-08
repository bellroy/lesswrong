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
from pylons import c, request, g
from pylons.i18n import _
from pylons.controllers.util import abort
from r2.lib import utils, captcha
from r2.lib.filters import unkeep_space, websafe, _force_unicode
from r2.lib.db.operators import asc, desc
from r2.config import cache
from r2.lib.template_helpers import add_sr
from r2.lib.jsonresponse import json_respond

from r2.models import *

from r2.controllers.errors import errors, UserRequiredException

from copy import copy
from datetime import datetime, timedelta
import re

class Validator(object):
    default_param = None
    def __init__(self, param=None, default=None, post=True, get=True, url=True):
        if param:
            self.param = param
        else:
            self.param = self.default_param

        self.default = default
        self.post, self.get, self.url = post, get, url

    def __call__(self, url):
        a = []
        if self.param:
            for p in utils.tup(self.param):
                if self.post and request.post.get(p):
                    val = request.post[p]
                elif self.get and request.get.get(p):
                    val = request.get[p]
                elif self.url and url.get(p):
                    val = url[p]
                else:
                    val = self.default
                a.append(val)
        return self.run(*a)

def validate(*simple_vals, **param_vals):
    def val(fn):
        def newfn(self, *a, **env):
            try:
                for validator in simple_vals:
                    validator(env)
                
                kw = self.build_arg_list(fn, env)
                for var, validator in param_vals.iteritems():
                    kw[var] = validator(env)
                
                return fn(self, *a, **kw)

            except UserRequiredException:
                if request.method == "POST" and hasattr(self, "ajax_login_redirect"):
                    # ajax failure, so redirect accordingly
                    return  self.ajax_login_redirect("/")
                return self.intermediate_redirect('/login')
        return newfn
    return val


#### validators ####
class nop(Validator):
    def run(self, x):
        return x

class VLang(Validator):
    def run(self, lang):
        if lang:
            lang = str(lang.split('[')[1].strip(']'))
            if lang in g.all_languages:
                return lang
        #else
        return 'en'

class VRequired(Validator):
    def __init__(self, param, error, *a, **kw):
        Validator.__init__(self, param, *a, **kw)
        self._error = error

    def error(self, e = None):
        if not e: e = self._error
        if e:
            c.errors.add(e)
        
    def run(self, item):
        if not item:
            self.error()
        else:
            return item

class VLink(Validator):
    def __init__(self, param, redirect = True, *a, **kw):
        Validator.__init__(self, param, *a, **kw)
        self.redirect = redirect
    
    def run(self, link_id):
        if link_id:
            try:
                aid = int(link_id, 36)
                return Link._byID(aid, True)
            except (NotFound, ValueError):
                if self.redirect:
                    abort(404, 'page not found')
                else:
                    return None

class VTagByName(Validator):
    def __init__(self, param, *a, **kw):
        Validator.__init__(self, param, *a, **kw)
        
    def run(self, name):
        if name:
            try:
                return Tag._by_name(name)
            except NotFound:
                abort(404, 'page not found')

class VTags(Validator):
    comma_sep = re.compile('[,\s]+', re.UNICODE)
    
    def __init__(self, param, *a, **kw):
        Validator.__init__(self, param, *a, **kw)
        
    def run(self, tag_field):
        tags = []
        if tag_field:
            # Tags are comma delimited
            tags = self.comma_sep.split(tag_field)
        return tags

class VMessage(Validator):
    def run(self, message_id):
        if message_id:
            try:
                aid = int(message_id, 36)
                return Message._byID(aid, True)
            except (NotFound, ValueError):
                abort(404, 'page not found')


class VCommentID(Validator):
    def run(self, cid):
        if cid:
            try:
                cid = int(cid, 36)
                return Comment._byID(cid, True)
            except (NotFound, ValueError):
                pass

class VCount(Validator):
    def run(self, count):
        if count is None:
            count = 0
        return max(int(count), 0)


class VLimit(Validator):
    def run(self, limit):
        if limit is None:
            return c.user.pref_numsites 
        return min(max(int(limit), 1), 250)

class VCssMeasure(Validator):
    measure = re.compile(r"^\s*[\d\.]+\w{0,3}\s*$")
    def run(self, value):
        return value if value and self.measure.match(value) else ''

subreddit_rx = re.compile(r"^[\w]{3,20}$", re.UNICODE)

def chksrname(x):
    #notice the space before reddit.com
    if x in ('friends', 'all', ' reddit.com'):
        return False

    try:
        return str(x) if x and subreddit_rx.match(x) else None
    except UnicodeEncodeError:
        return None


class VLinkFullnames(Validator):
    "A space- or comma-separated list of fullnames for Links"
    valid_re = re.compile(r'^(' + Link._type_prefix + str(Link._type_id) +
                          r'_[0-9a-z]+[ ,]?)+$')
    splitter = re.compile('[ ,]+')

    def __init__(self, item, *a, **kw):
        self.item = item
        Validator.__init__(self, item, *a, **kw)
    
    def run(self, val):
        if val and self.valid_re.match(val):
            return self.splitter.split(val)
    
class VLength(Validator):
    def __init__(self, item, length = 10000,
                 empty_error = errors.BAD_COMMENT,
                 length_error = errors.COMMENT_TOO_LONG, **kw):
        Validator.__init__(self, item, **kw)
        self.length = length
        self.len_error = length_error
        self.emp_error = empty_error

    def run(self, title):
        if not title:
            if self.emp_error is not None:
                c.errors.add(self.emp_error)
        elif len(title) > self.length:
            c.errors.add(self.len_error)
        else:
            return title
        
class VTitle(VLength):
    only_whitespace = re.compile(r"^\s*$", re.UNICODE)
    
    def __init__(self, item, length = 200, **kw):
        VLength.__init__(self, item, length = length,
                         empty_error = errors.NO_TITLE,
                         length_error = errors.TITLE_TOO_LONG, **kw)

    def run(self, title):
        title = VLength.run(self, title)
        if title and self.only_whitespace.match(title):
            c.errors.add(errors.NO_TITLE)
        else:
            return title
    
class VComment(VLength):
    def __init__(self, item, length = 10000, **kw):
        VLength.__init__(self, item, length = length, **kw)

        
class VMessage(VLength):
    def __init__(self, item, length = 10000, **kw):
        VLength.__init__(self, item, length = length, 
                         empty_error = errors.NO_MSG_BODY, **kw)


class VSubredditName(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.BAD_SR_NAME, *a, **kw)

    def run(self, name):
        name = chksrname(name)
        if not name:
            return self.error()
        else:
            try:
                a = Subreddit._by_name(name)
                return self.error(errors.SUBREDDIT_EXISTS)
            except NotFound:
                return name

class VSubredditTitle(Validator):
    def run(self, title):
        if not title:
            c.errors.add(errors.NO_TITLE)
        elif len(title) > 100:
            c.errors.add(errors.TITLE_TOO_LONG)
        else:
            return title

class VSubredditDesc(Validator):
    def run(self, description):
        if description and len(description) > 500:
            c.errors.add(errors.DESC_TOO_LONG)
        return unkeep_space(description or '')

class VAccountByName(VRequired):
    def __init__(self, param, error = errors.USER_DOESNT_EXIST, *a, **kw):
        VRequired.__init__(self, param, error, *a, **kw)
        
    def run(self, name):
        if name:
            try:
                return Account._by_name(name)
            except NotFound: pass
        return self.error()

class VByName(VRequired):
    def __init__(self, param, 
                 error = errors.NO_THING_ID, *a, **kw):
        VRequired.__init__(self, param, error, *a, **kw)

    def run(self, fullname):
        if fullname:
            try:
                return Thing._by_fullname(fullname, False, data=True)
            except NotFound:
                pass
        return self.error()

class VByNameIfAuthor(VByName):
    def run(self, fullname):
        thing = VByName.run(self, fullname)
        if thing:
            if not thing._loaded: thing._load()
            if c.user_is_loggedin and thing.author_id == c.user._id:
                return thing
        return self.error(errors.NOT_AUTHOR)

class VCaptcha(Validator):
    default_param = ('iden', 'captcha')
    
    def run(self, iden, solution):
        if (not c.user_is_loggedin or c.user.needs_captcha()):
            if not captcha.valid_solution(iden, solution):
                c.errors.add(errors.BAD_CAPTCHA)

class VUser(Validator):
    def run(self, password = None):
        if not c.user_is_loggedin:
            raise UserRequiredException

        if (password is not None) and not valid_password(c.user, password):
            c.errors.add(errors.WRONG_PASSWORD)
            
class VModhash(Validator):
    default_param = 'uh'
    def run(self, uh):
        pass

class VVotehash(Validator):
    def run(self, vh, thing_name):
        return True

class VAdmin(Validator):
    def run(self):
        if not c.user_is_admin:
            abort(404, "page not found")

class VSponsor(Validator):
    def run(self):
        if not c.user_is_sponsor:
            abort(403, 'forbidden')

class VSrModerator(Validator):
    def run(self):
        if not (c.user_is_loggedin and c.site.is_moderator(c.user) 
                or c.user_is_admin):
            abort(403, "forbidden")

class VSrCanBan(Validator):
    def run(self, thing_name):
        if c.user_is_admin:
            return True
        elif c.user_is_loggedin:
            item = Thing._by_fullname(thing_name,data=True)
            # will throw a legitimate 500 if this isn't a link or
            # comment, because this should only be used on links and
            # comments
            subreddit = item.subreddit_slow
            if subreddit.can_ban(c.user):
                return True
        abort(403,'forbidden')

class VSrSpecial(Validator):
    def run(self, thing_name):
        if c.user_is_admin:
            return True
        elif c.user_is_loggedin:
            item = Thing._by_fullname(thing_name,data=True)
            # will throw a legitimate 500 if this isn't a link or
            # comment, because this should only be used on links and
            # comments
            subreddit = item.subreddit_slow
            if subreddit.is_special(c.user):
                return True
        abort(403,'forbidden')

class VSRSubmitPage(Validator):
    def run(self):
        if not (c.default_sr or c.user_is_loggedin and 
                c.site.can_submit(c.user)):
            abort(403, "forbidden")

class VSubmitParent(Validator):
    def run(self, fullname):
        if fullname:
            parent = Thing._by_fullname(fullname, False, data=True)
            if isinstance(parent, Message):
                return parent
            else:
                sr = parent.subreddit_slow
                if c.user_is_loggedin and sr.can_comment(c.user):
                    return parent
        #else
        abort(403, "forbidden")
        
class VSubmitLink(VLink):
    def __init__(self, param, redirect = True, *a, **kw):
        VLink.__init__(self, param, redirect = redirect, *a, **kw)
        
    def run(self, link_name):
        link = VLink.run(self, link_name)
        if link and not (c.user_is_loggedin and link.can_submit(c.user)):
            abort(403, "forbidden")
        return link

class VSubmitSR(Validator):
    def run(self, sr_name):
        try:
            sr = Subreddit._by_name(sr_name)
        except NotFound:
            c.errors.add(errors.SUBREDDIT_NOEXIST)
            sr = None

        if sr and not (c.user_is_loggedin and sr.can_submit(c.user)):
            c.errors.add(errors.SUBREDDIT_FORBIDDEN)
            sr = None

        return sr
        
pass_rx = re.compile(r".{3,20}")

def chkpass(x):
    return x if x and pass_rx.match(x) else None

class VPassword(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.BAD_PASSWORD, *a, **kw)
    def run(self, password, verify):
        if not chkpass(password):
            return self.error()
        elif verify != password:
            return self.error(errors.BAD_PASSWORD_MATCH)
        else:
            return password

user_rx = re.compile(r"^[\w-]{3,20}$", re.UNICODE)

def chkuser(x):
    try:
        return str(x) if user_rx.match(x) else None
    except TypeError:
        return None
    except UnicodeEncodeError:
        return None

def whyuserbad(x):
    if len(x)<3:
        return errors.BAD_USERNAME_SHORT
    if len(x)>20:
        return errors.BAD_USERNAME_LONG
    return errors.BAD_USERNAME_CHARS

class VUname(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.BAD_USERNAME, *a, **kw)
    def run(self, user_name):
        original_user_name = user_name;
        user_name = chkuser(user_name)
        if not user_name:
            return self.error(whyuserbad(original_user_name))
        else:
            try:
                a = Account._by_name(user_name, True)
                return self.error(errors.USERNAME_TAKEN)
            except NotFound:
                return user_name

class VLogin(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.WRONG_PASSWORD, *a, **kw)
        
    def run(self, user_name, password):
        user_name = chkuser(user_name)
        user = None
        if user_name:
            user = valid_login(user_name, password)
        if not user:
            return self.error()
        return user


class VSanitizedUrl(Validator):
    def run(self, url):
        return utils.sanitize_url(url)

class VUserWebsiteUrl(VSanitizedUrl):
    def run(self, url):
        val = VSanitizedUrl.run(self, url)
        if val is None:
            return ''
        else:
            return val

class VUrl(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.NO_URL, *a, **kw)

    def run(self, url, sr = None):
        if sr is None and not isinstance(c.site, FakeSubreddit):
            sr = c.site
        elif sr:
            try:
                sr = Subreddit._by_name(sr)
            except NotFound:
                c.errors.add(errors.SUBREDDIT_NOEXIST)
                sr = None
        else:
            sr = None
        
        if not url:
            return self.error(errors.NO_URL)
        url = utils.sanitize_url(url)
        if url == 'self':
            return url
        elif url:
            try:
                l = Link._by_url(url, sr)
                self.error(errors.ALREADY_SUB)
                return utils.tup(l)
            except NotFound:
                return url
        return self.error(errors.BAD_URL)

class VExistingUname(VRequired):
    def __init__(self, item, *a, **kw):
        VRequired.__init__(self, item, errors.NO_USER, *a, **kw)

    def run(self, name):
        if name:
            try:
                return Account._by_name(name)
            except NotFound:
                return self.error(errors.USER_DOESNT_EXIST)
        self.error()

class VUserWithEmail(VExistingUname):
    def run(self, name):
        user = VExistingUname.run(self, name)
        if not user or not hasattr(user, 'email') or not user.email:
            return self.error(errors.NO_EMAIL_FOR_USER)
        return user
            

class VBoolean(Validator):
    def run(self, val):
        return val != "off" and bool(val)

class VLocation(VLength):
    def __init__(self, item, length = 100, **kw):
        VLength.__init__(self, item, length = length, 
                         length_error = errors.LOCATION_TOO_LONG,
                         empty_error = None, **kw)

    def run(self, val):
        val = VLength.run(self, val)
        if val == None:
            return ''
        else:
            return val

class VInt(Validator):
    def __init__(self, param, min=None, max=None, *a, **kw):
        self.min = min
        self.max = max
        Validator.__init__(self, param, *a, **kw)

    def run(self, val):
        if not val:
            return

        try:
            val = int(val)
            if self.min is not None and val < self.min:
                val = self.min
            elif self.max is not None and val > self.max:
                val = self.max
            return val
        except ValueError:
            c.errors.add(errors.BAD_NUMBER)

class VCssName(Validator):
    """
    returns a name iff it consists of alphanumeric characters and
    possibly "-", and is below the length limit.
    """
    r_css_name = re.compile(r"^[a-zA-Z0-9\-]{1,100}$")
    def run(self, name):
        if name and self.r_css_name.match(name):
            return name
    
class VMenu(Validator):

    def __init__(self, param, menu_cls, remember = True, **kw):
        self.nav = menu_cls
        self.remember = remember
        param = (menu_cls.get_param, param)
        Validator.__init__(self, param, **kw)

    def run(self, sort, where):
        if self.remember:
            pref = "%s_%s" % (where, self.nav.get_param)
            user_prefs = copy(c.user.sort_options) if c.user else {}
            user_pref = user_prefs.get(pref)
    
            # check to see if a default param has been set
            if not sort:
                sort = user_pref
            
        # validate the sort
        if sort not in self.nav.options:
            sort = self.nav.default

        # commit the sort if changed
        if self.remember and c.user_is_loggedin and sort != user_pref:
            user_prefs[pref] = sort
            c.user.sort_options = user_prefs
            user = c.user
            utils.worker.do(lambda: user._commit())

        return sort
            

class VRatelimit(Validator):
    def __init__(self, rate_user = False, rate_ip = False,
                 prefix = 'rate_', *a, **kw):
        self.rate_user = rate_user
        self.rate_ip = rate_ip
        self.prefix = prefix
        Validator.__init__(self, *a, **kw)

    def run (self):
        to_check = []
        if self.rate_user and c.user_is_loggedin:
            to_check.append('user' + str(c.user._id36))
        if self.rate_ip:
            to_check.append('ip' + str(request.ip))

        r = cache.get_multi(to_check, self.prefix)
        if r:
            expire_time = max(r.values())
            time = utils.timeuntil(expire_time)
            c.errors.add(errors.RATELIMIT, {'time': time})

    @classmethod
    def ratelimit(self, rate_user = False, rate_ip = False, prefix = "rate_"):
        to_set = {}
        seconds = g.RATELIMIT*60
        expire_time = datetime.now(g.tz) + timedelta(seconds = seconds)
        if rate_user and c.user_is_loggedin:
            to_set['user' + str(c.user._id36)] = expire_time
        if rate_ip:
            to_set['ip' + str(request.ip)] = expire_time

        cache.set_multi(to_set, prefix, time = seconds)

class VCommentIDs(Validator):
    #id_str is a comma separated list of id36's
    def run(self, id_str):
        cids = [int(i, 36) for i in id_str.split(',')]
        comments = Comment._byID(cids, data=True, return_dict = False)
        return comments

class VFullNames(Validator):
    #id_str is a comma separated list of id36's
    def run(self, id_str):
        tids = id_str.split(',')
        return Thing._by_fullname(tids, data=True, return_dict = False)

class VSubreddits(Validator):
    #the subreddits are just in the post, this is for the my.reddit pref page
    def run(self):
        subreddits = Subreddit._by_fullname(request.post.keys())
        return subreddits.values()

class VCacheKey(Validator):
    def __init__(self, cache_prefix, param, *a, **kw):
        self.cache_prefix = cache_prefix
        Validator.__init__(self, param, *a, **kw)

    def run(self, key, name):
        if key:
            uid = cache.get(str(self.cache_prefix + "_" + key))
            try:
                a = Account._byID(uid, data = True)
            except NotFound:
                return None
            if name and a.name.lower() != name.lower():
                c.errors.add(errors.BAD_USERNAME)
            if a:
                return a
        c.errors.add(errors.EXPIRED)

class VOneOf(Validator):
    def __init__(self, param, options = (), *a, **kw):
        Validator.__init__(self, param, *a, **kw)
        self.options = options

    def run(self, val):
        if self.options and val not in self.options:
            c.errors.add(errors.INVALID_OPTION)
            return self.default
        else:
            return val

class VReason(Validator):
    def run(self, reason):
        if not reason:
            return

        if reason.startswith('redirect_'):
            dest = reason[9:]
            if (not dest.startswith(c.site.path) and 
                not dest.startswith("http:")):
                dest = (c.site.path + dest).replace('//', '/')
            return ('redirect', dest)
        if reason.startswith('vote_'):
            fullname = reason[5:]
            t = Thing._by_fullname(fullname, data=True)
            return ('redirect', t.make_permalink_slow())
        elif reason.startswith('share_'):
            fullname = reason[6:]
            t = Thing._by_fullname(fullname, data=True)
            return ('redirect', t.make_permalink_slow())
        elif reason.startswith('reply_'):
            fullname = reason[6:]
            t = Thing._by_fullname(fullname, data=True)
            return ('redirect', t.make_permalink_slow())
        elif reason.startswith('sr_change_'):
            sr_list = reason[10:].split(',')
            fullnames = dict(i.split(':') for i in sr_list)
            srs = Subreddit._by_fullname(fullnames.keys(), data = True,
                                         return_dict = False)
            sr_onoff = dict((sr, fullnames[sr._fullname] == 1) for sr in srs)
            return ('subscribe', sr_onoff)


class ValidEmails(Validator):
    """Validates a list of email addresses passed in as a string and
    delineated by whitespace, ',' or ';'.  Also validates quantity of
    provided emails.  Returns a list of valid email addresses on
    success"""
    
    separator = re.compile(r'[^\s,;]+')
    email_re  = re.compile(r'.+@.+\..+')

    def __init__(self, param, num = 20, **kw):
        self.num = num
        Validator.__init__(self, param = param, **kw)
        
    def run(self, emails0):
        emails = set(self.separator.findall(emails0) if emails0 else [])
        failures = set(e for e in emails if not self.email_re.match(e))
        emails = emails - failures

        # make sure the number of addresses does not exceed the max
        if self.num > 0 and len(emails) + len(failures) > self.num:
            # special case for 1: there should be no delineators at all, so
            # send back original string to the user
            if self.num == 1:
                c.errors.add(errors.BAD_EMAILS,
                             {'emails': '"%s"' % emails0})
            # else report the number expected
            else:
                c.errors.add(errors.TOO_MANY_EMAILS,
                             {'num': self.num})
        # correct number, but invalid formatting
        elif failures:
            c.errors.add(errors.BAD_EMAILS,
                         {'emails': ', '.join(failures)})
        # no emails
        elif not emails:
            c.errors.add(errors.NO_EMAILS)
        else:
            # return single email if one is expected, list otherwise
            return list(emails)[0] if self.num == 1 else emails


class VCnameDomain(Validator):
    domain_re  = re.compile(r'^([\w]+\.)+[\w]+$')

    def run(self, domain):
        if (domain
            and (not self.domain_re.match(domain)
                 or domain.endswith('.reddit.com')
                 or len(domain) > 300)):
            c.errors.add(errors.BAD_CNAME)
        elif domain:
            try:
                return str(domain).lower()
            except UnicodeEncodeError:
                c.errors.add(errors.BAD_CNAME)




# NOTE: make sure *never* to have res check these are present
# otherwise, the response could contain reference to these errors...!
class ValidIP(Validator):
    def run(self):
        if is_banned_IP(request.ip):
            c.errors.add(errors.BANNED_IP)
        return request.ip

class ValidDomain(Validator):
    def run(self, url):
        if url and is_banned_domain(url):
            c.errors.add(errors.BANNED_DOMAIN)
