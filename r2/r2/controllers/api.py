# -*- coding: utf-8 -*-
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
from reddit_base import RedditController

from pylons.i18n import _
from pylons import c, request, response
from pylons.controllers.util import etag_cache

import hashlib
from validator import *

from r2.models import *
from r2.models.subreddit import Default as DefaultSR
import r2.models.thing_changes as tc

from r2.controllers import ListingController

from r2.lib.utils import get_title, sanitize_url, timeuntil, \
    set_last_modified, remote_addr
from r2.lib.utils import query_string, to36, timefromnow
from r2.lib.wrapped import Wrapped
from r2.lib.pages import FriendList, ContributorList, ModList, EditorList, \
    BannedList, BoringPage, FormPage, NewLink, CssError, UploadedImage, \
    RecentArticles, RecentComments, TagCloud, TopContributors, TopMonthlyContributors, WikiPageList, \
    ArticleNavigation, UpcomingMeetups, RecentPromotedArticles, \
    MeetupsMap


from r2.lib.menus import CommentSortMenu
from r2.lib.translation import Translator
from r2.lib.normalized_hot import expire_hot
from r2.lib.captcha import get_iden
from r2.lib import emailer
from r2.lib.strings import strings
from r2.lib.memoize import clear_memo
from r2.lib.filters import _force_unicode
from r2.lib.db import queries
from r2.config import cache
from r2.lib.jsonresponse import JsonResponse, Json
from r2.lib.jsontemplates import api_type
from r2.lib import cssfilter
from r2.lib import tracking
from r2.lib.media import force_thumbnail, thumbnail_url
from r2.lib.comment_tree import add_comment, delete_comment

from datetime import datetime, timedelta
from simplejson import dumps
from md5 import md5

from r2.lib.promote import promote, unpromote, get_promoted

def link_listing_by_url(url, count = None):
    try:
        links = list(tup(Link._by_url(url, sr = c.site)))
        links.sort(key = lambda x: -x._score)
        if count is not None:
            links = links[:count]
    except NotFound:
        links = ()

    names = [l._fullname for l in links]
    builder = IDBuilder(names, num = 25)
    listing = LinkListing(builder).listing()
    return listing


class ApiController(RedditController):
    def response_func(self, **kw):
        return self.sendstring(dumps(kw))

    @Json
    def ajax_login_redirect(self, res, dest):
        res._redirect("/login" + query_string(dict(dest=dest)))

    def link_exists(self, url, sr, message = False):
        try:
            l = Link._by_url(url, sr)
            if message:
                return l.already_submitted_link()
            else:
                return l.make_permalink_slow()
        except NotFound:
            pass


    @validate(url = nop("url"),
              sr = VSubredditName,
              count = VLimit('limit'))
    def GET_info(self, url, sr, count):
        listing = link_listing_by_url(url, count = count)
        res = BoringPage(_("API"),
                         content = listing).render()
        return res

    @Json
    @validate(VCaptcha(),
              name=VRequired('name', errors.NO_NAME),
              email=VRequired('email', errors.NO_EMAIL),
              replyto = nop('replyto'),
              reason = nop('reason'),
              message=VRequired('message', errors.NO_MESSAGE))
    def POST_feedback(self, res, name, email, replyto, reason, message):
        res._update('status', innerHTML = '')
        if res._chk_error(errors.NO_NAME):
            res._focus("name")
        elif res._chk_error(errors.NO_EMAIL):
            res._focus("email")
        elif res._chk_error(errors.NO_MESSAGE):
            res._focus("personal")
        elif res._chk_captcha(errors.BAD_CAPTCHA):
            pass

        if not res.error:
            if reason != 'ad_inq':
                emailer.feedback_email(email, message, name = name or '',
                                       reply_to = replyto or '')
            else:
                emailer.ad_inq_email(email, message, name = name or '',
                                       reply_to = replyto or '')
            res._update('success',
                        innerHTML=_("Thanks for your message! you should hear back from us shortly."))
            res._update("personal", value='')
            res._update("captcha", value='')
            res._hide("wtf")
    POST_ad_inq = POST_feedback

    @Json
    @validate(VCaptcha(),
              VUser(),
              VModhash(),
              ip = ValidIP(),
              to = VExistingUname('to'),
              subject = VRequired('subject', errors.NO_SUBJECT),
              body = VMessage('message'))
    def POST_compose(self, res, to, subject, body, ip):
        res._update('status', innerHTML='')
        if (res._chk_error(errors.NO_USER) or
            res._chk_error(errors.USER_DOESNT_EXIST)):
            res._focus('to')
        elif res._chk_error(errors.NO_SUBJECT):
            res._focus('subject')
        elif (res._chk_error(errors.NO_MSG_BODY) or
              res._chk_error(errors.COMMENT_TOO_LONG)):
            res._focus('message')
        elif res._chk_captcha(errors.BAD_CAPTCHA):
            pass

        if not res.error:
            spam = (c.user._spam or
                    errors.BANNED_IP in c.errors or
                    errors.BANNED_DOMAIN in c.errors)

            m, inbox_rel = Message._new(c.user, to, subject, body, ip, spam)
            res._update('success',
                        innerHTML=_("Your message has been delivered"))
            res._update('to', value='')
            res._update('subject', value='')
            res._update('message', value='')

            if g.write_query_queue:
                queries.new_message(m, inbox_rel)
        else:
            res._update('success', innerHTML='')

    @Json
    @validate(VAdmin(),
              link = VByName('id'))
    def POST_bless(self, res, link):
        link.set_blessed(True)

    @Json
    @validate(VAdmin(),
              link = VByName('id'))
    def POST_unbless(self, res, link):
        link.set_blessed(False)

    @Json
    @validate(VUser(),
              VCaptcha(),
              VRatelimit(rate_user = True, rate_ip = True, prefix='rate_submit_'),
              VModhash(),
              ip = ValidIP(),
              sr = VSubmitSR('sr'),
              title = VTitle('title'),
              l = VLink('article_id'),
              new_content = nop('article'),
              save = nop('save'),
              continue_editing = VBoolean('keep_editing'),
              notify_on_comment = VBoolean('notify_on_comment'),
              tags = VTags('tags'))
    def POST_submit(self, res, l, new_content, title, save, continue_editing, sr, ip, tags, notify_on_comment):
        res._update('status', innerHTML = '')
        should_ratelimit = sr.should_ratelimit(c.user, 'link') if sr else True

        #remove the ratelimit error if the user's karma is high
        if not should_ratelimit:
            c.errors.remove(errors.RATELIMIT)

        #ratelimiter
        if res._chk_error(errors.RATELIMIT):
            pass
        # check for title, otherwise look it up and return it
        elif res._chk_error(errors.NO_TITLE):
            # clear out this error
            res._chk_error(errors.TITLE_TOO_LONG)
            res._focus('title')
        elif res._chk_error(errors.TITLE_TOO_LONG):
            res._focus('title')
        elif res._chk_captcha(errors.BAD_CAPTCHA):
            pass
        elif res._chk_error(errors.SUBREDDIT_FORBIDDEN):
            pass


        if res.error or not title: return

        # check whether this is spam:
        spam = (c.user._spam or
                errors.BANNED_IP in c.errors or
                errors.BANNED_DOMAIN in c.errors)

        if not new_content:
            new_content = ''

        # well, nothing left to do but submit it
        # TODO: include article body in arguments to Link model
        # print "\n".join(request.post.va)
        if not l:
          l = Link._submit(request.post.title, new_content, c.user, sr, ip, tags, spam,
                           notify_on_comment=notify_on_comment)
          if save == 'on':
              r = l._save(c.user)
              if g.write_query_queue:
                  queries.new_savehide(r)
          
          #set the ratelimiter
          if should_ratelimit:
              VRatelimit.ratelimit(rate_user=True, rate_ip = True, prefix='rate_submit_')

          #update the queries
          if g.write_query_queue:
              queries.new_link(l)
        else:
          edit = None
          if c.user._id != l.author_id:
            edit = Edit._new(l,c.user,new_content)
          old_url = l.url
          l.title = request.post.title
          l.set_article(new_content)
          l.notify_on_comment = notify_on_comment
          l.change_subreddit(sr._id)
          l._commit()
          l.set_tags(tags)
          l.update_url_cache(old_url)
          if edit:
            edit._commit()

        #update the modified flags
        set_last_modified(c.user, 'overview')
        set_last_modified(c.user, 'submitted')

        # flag search indexer that something has changed
        tc.changed(l)

        if continue_editing:
          path = "/edit/%s" % l._id36
        else:
          # make_permalink is designed for links that can be set to _top
          # here, we need to generate an ajax redirect as if we were not on a
          # cname.
          cname = c.cname
          c.cname = False
          #path = l.make_permalink_slow()
          path = l.make_permalink(sr, sr_path = not sr.name == g.default_sr)
          c.cname = cname

        res._redirect(path)


    def _login(self, res, user, dest='', rem = None):
        self.login(user, rem = rem)
        dest = dest or request.referer or '/'
        res._redirect(dest)

    @Json
    @validate(user = VLogin(['user_login', 'passwd_login']),
              op = VOneOf('op', options = ("login-main", "reg", "login"),
                          default = 'login'),
              dest = nop('dest'),
              rem = nop('rem'),
              reason = VReason('reason'))
    def POST_login(self, res, user, op, dest, rem, reason):
        if reason and reason[0] == 'redirect':
            dest = reason[1]

        res._update('status_' + op, innerHTML='')
        if res._chk_error(errors.WRONG_PASSWORD, op):
            res._focus('passwd_' + op)
        else:
            self._login(res, user, dest, rem == 'on')


    @Json
    @validate(VCaptcha(),
              VRatelimit(rate_ip = True, prefix='rate_register_'),
              name = VUname(['user_reg']),
              email = nop('email_reg'),
              password = VPassword(['passwd_reg', 'passwd2_reg']),
              op = VOneOf('op', options = ("login-main", "reg", "login"),
                          default = 'login'),
              dest = nop('dest'),
              rem = nop('rem'),
              reason = VReason('reason'))
    def POST_register(self, res, name, email, password, op, dest, rem, reason):
        res._update('status_' + op, innerHTML='')
        if res._chk_error(errors.BAD_USERNAME, op):
            res._focus('user_reg')
        elif res._chk_error(errors.BAD_USERNAME_SHORT, op):
            res._focus('user_reg')
        elif res._chk_error(errors.BAD_USERNAME_LONG, op):
            res._focus('user_reg')
        elif res._chk_error(errors.BAD_USERNAME_CHARS, op):
            res._focus('user_reg')
        elif res._chk_error(errors.USERNAME_TAKEN, op):
            res._focus('user_reg')
        elif res._chk_error(errors.BAD_PASSWORD, op):
            res._focus('passwd_reg')
        elif res._chk_error(errors.BAD_PASSWORD_MATCH, op):
            res._focus('passwd2_reg')
        elif res._chk_error(errors.DRACONIAN, op):
            res._focus('legal_reg')
        elif res._chk_captcha(errors.BAD_CAPTCHA):
            pass
        elif res._chk_error(errors.RATELIMIT, op):
            pass

        if res.error:
            return

        user = register(name, password)
        VRatelimit.ratelimit(rate_ip = True, prefix='rate_register_')

        #anything else we know (email, languages)?
        if email:
            user.email = email

        user.pref_lang = c.lang
        if c.content_langs == 'all':
            user.pref_content_langs = 'all'
        else:
            langs = list(c.content_langs)
            langs.sort()
            user.pref_content_langs = tuple(langs)

        d = c.user._dirties.copy()
        user._commit()

        c.user = user

        # Create a drafts subredit for this user
        sr = Subreddit._create_and_subscribe(
            user.draft_sr_name, user, {
                'title': "Drafts for " + user.name,
                'type': "private",
                'default_listing': 'new',
            }
        )

        if reason:
            if reason[0] == 'redirect':
                dest = reason[1]
            elif reason[0] == 'subscribe':
                for sr, sub in reason[1].iteritems():
                    self._subscribe(sr, sub)

        self._login(res, user, dest, rem)


    @Json
    @validate(VUser(),
              VModhash(),
              container = VByName('id'),
              type = VOneOf('location', ('moderator',  'contributor')))
    def POST_leave(self, res, container, type):
        if container and c.user:
            res._hide("pre_" + container._fullname)
            res._hide("thingrow_" + container._fullname)
            fn = getattr(container, 'remove_' + type)
            fn(c.user)

    @Json
    @validate(VUser(),
              VModhash(),
              ip = ValidIP(),
              action = VOneOf('action', ('add', 'remove')),
              redirect = nop('redirect'),
              friend = VExistingUname('name'),
              container = VByName('container'),
              type = VOneOf('type', ('friend', 'moderator', 'editor', 'contributor', 'banned')))
    def POST_friend(self, res, ip, friend, action, redirect, container, type):
        res._update('status', innerHTML='')

        fn = getattr(container, action + '_' + type)

        if (not c.user_is_admin
            and (type in ('moderator','contributer','banned')
                 and not c.site.is_moderator(c.user))):

            abort(403,'forbidden')
        elif type == 'editor' and not c.user_is_admin:
            abort(403,'forbidden')
        elif action == 'add':
            if res._chk_errors((errors.USER_DOESNT_EXIST,
                                errors.NO_USER)):
                res._focus('name')
            else:
                new = fn(friend)
                cls = dict(friend=FriendList,
                           moderator=ModList,
                           editor=EditorList,
                           contributor=ContributorList,
                           banned=BannedList).get(type)
                res._update('name', value = '')

                #subscribing doesn't need a response
                if new and cls:
                    res.object = cls().ajax_user(friend).for_ajax('add')

                    if type != 'friend':
                        msg = strings.msg_add_friend.get(type)
                        subj = strings.subj_add_friend.get(type)
                        if msg and subj and friend.name != c.user.name:
                            # fullpath with domain needed or the markdown link
                            # will break
                            d = dict(url = container.path,
                                     title = container.title)
                            msg = msg % d
                            subj = subj % d
                            Message._new(c.user, friend, subj, msg, ip,
                                         c.user._spam)
        elif action == 'remove' and friend:
            fn(friend)


    @Json
    @validate(VUser('curpass', default = ''),
              VModhash(),
              curpass = nop('curpass'),
              email = ValidEmails("email", num = 1),
              newpass = nop("newpass"),
              verpass = nop("verpass"),
              password = VPassword(['newpass', 'verpass']))
    def POST_update(self, res, email, curpass, password, newpass, verpass):
        res._update('status', innerHTML='')
        if res._chk_error(errors.WRONG_PASSWORD):
            res._focus('curpass')
            res._update('curpass', value='')
            return
        updated = False
        if res._chk_error(errors.BAD_EMAILS):
            res._focus('email')
        elif email and (not hasattr(c.user,'email')
                        or c.user.email != email):
            c.user.email = email
            c.user._commit()
            res._update('status',
                        innerHTML=_('Your email has been updated'))
            updated = True

        if newpass or verpass:
            if res._chk_error(errors.BAD_PASSWORD):
                res._focus('newpass')
            elif res._chk_error(errors.BAD_PASSWORD_MATCH):
                res._focus('verpass')
                res._update('verpass', value='')
            else:
                change_password(c.user, password)
                if updated:
                    res._update('status',
                                innerHTML=_('Your email and password have been updated'))
                else:
                    res._update('status',
                                innerHTML=_('Your password has been updated'))
                self.login(c.user)

    @Json
    @validate(VUser(),
              VModhash(),
              areyousure1 = nop('areyousure1'),
              areyousure2 = nop('areyousure2'),
              areyousure3 = nop('areyousure3'))
    def POST_delete_user(self, res, areyousure1, areyousure2, areyousure3):
        if areyousure1 == areyousure2 == areyousure3 == 'Yes':
            c.user.delete()
            res._redirect('/?deleted=true')
        else:
            res._update('status',
                        innerHTML = _("See? you don't really want to leave"))

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByNameIfAuthor('id'))
    def POST_del(self, res, thing):
        '''for deleting all sorts of things'''

        # Special check if comment can be deleted
        if isinstance(thing, Comment) and (not thing.can_delete()):
            res._set_error(errors.CANNOT_DELETE)
            return

        thing._deleted = True
        thing._commit()

        # flag search indexer that something has changed
        tc.changed(thing)

        #expire the item from the sr cache
        if isinstance(thing, Link):
            sr = thing.subreddit_slow
            expire_hot(sr)
            if g.use_query_cache:
                queries.new_link(thing)

        #comments have special delete tasks
        elif isinstance(thing, Comment):
            thing._delete()
            delete_comment(thing)
            if g.use_query_cache:
                queries.new_comment(thing, None)

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByNameIfAuthor('id'))
    def POST_retract(self, res, thing):
        '''for retracting comments'''

        if isinstance(thing, Comment):
            thing.retracted = True
            thing._commit()
            if g.use_query_cache:
                queries.new_comment(thing, None)


    @Json
    @validate(VUser(), VModhash(),
              thing = VByName('id'))
    def POST_report(self, res, thing):
        '''for reporting...'''
        Report.new(c.user, thing)


    def _validate_comment_text(self, res, error_thing, text):
        # This needs access to `res` to set the displayed message. A Validator isn't flexible enough
        if text:
            try:
                parsepolls(text, None, dry_run = True)
            except PollError as ex:
                res._set_error(errors.BAD_POLL_SYNTAX, error_thing._fullname, ex.message)


    @Json
    @validate(VUser(), VModhash(),
              comment = VByNameIfAuthor('id'),
              body = VComment('comment'))
    def POST_editcomment(self, res, comment, body):
        self._validate_comment_text(res, comment, body)

        res._update('status_' + comment._fullname, innerHTML = '')

        if not res._chk_errors((errors.BAD_COMMENT, errors.COMMENT_TOO_LONG, errors.NOT_AUTHOR,
                                errors.BAD_POLL_SYNTAX),
                               comment._fullname):
            if not c.user_is_admin: comment.editted = True
            comment.set_body(body)
            res._send_things(comment)

            # flag search indexer that something has changed
            tc.changed(comment)


    @Json
    @validate(VUser(),
              VModhash(),
              VRatelimit(rate_user = True, rate_ip = True, prefix = "rate_comment_"),
              ip = ValidIP(),
              parent = VSubmitParent('id'),
              comment = VComment('comment'))
    def POST_comment(self, res, parent, comment, ip):
        #wipe out the status message
        res._update('status_' + parent._fullname, innerHTML = '')

        should_ratelimit = True
        adjust_karma = 0

        #check the parent type here cause we need that for the
        #ratelimit checks
        parent_comment = None
        if isinstance(parent, Message):
            is_message = True
            should_ratelimit = False
            link = None
        else:
            is_message = False
            is_comment = True
            if isinstance(parent, Link):
                link = parent
            else:
                link = Link._byID(parent.link_id, data = True)
                parent_comment = parent
            sr = parent.subreddit_slow
            if not sr.should_ratelimit(c.user, 'comment'):
                should_ratelimit = False

        if link and not link.comments_enabled:
            return abort(403,'forbidden')

        #remove the ratelimit error if the user's karma is high
        if not should_ratelimit:
            c.errors.remove(errors.RATELIMIT)

        # assess a tax on replies to downvoted comments
        if parent_comment and parent_comment.reply_costs_karma:
            if c.user.safe_karma < g.downvoted_reply_karma_cost:
                c.errors.add(errors.NOT_ENOUGH_KARMA)
            else:
                adjust_karma = -g.downvoted_reply_karma_cost

        # make sure there are no errors in poll syntax
        self._validate_comment_text(res, parent, comment)

        if res._chk_errors((errors.BAD_COMMENT, errors.COMMENT_TOO_LONG, errors.RATELIMIT,
                            errors.NOT_ENOUGH_KARMA, errors.BAD_POLL_SYNTAX),
                           parent._fullname):
            res._focus("comment_reply_" + parent._fullname)
            return
        res._show('reply_' + parent._fullname)
        res._update("comment_reply_" + parent._fullname, rows = '2')

        # now that all inputs are verified, we can begin performing destructive updates:

        if adjust_karma:
            KarmaAdjustment.store(c.user, sr, adjust_karma)
            c.user.incr_karma('adjustment', sr, adjust_karma)

        spam = (c.user._spam or
                errors.BANNED_IP in c.errors)

        if is_message:
            to = Account._byID(parent.author_id)
            subject = parent.subject
            re = "Re: "
            if not subject.startswith(re):
                subject = re + subject
            item, inbox_rel = Message._new(c.user, to, subject, comment, ip, spam)
            item.parent_id = parent._id
            res._send_things(item)
        else:
            item, inbox_rel =  Comment._new(c.user, link, parent_comment, comment,
                                            ip, spam)
            item.set_body(comment)  # some markup requires the comment to exist and have an ID before it can be parsed
            res._update("comment_reply_" + parent._fullname,
                        innerHTML='', value='')
            res._send_things(item)
            res._hide('noresults')

        #update the queries
        if g.write_query_queue:
            if is_message:
                queries.new_message(item, inbox_rel)
            else:
                queries.new_comment(item, inbox_rel)

        #set the ratelimiter
        if should_ratelimit:
            VRatelimit.ratelimit(rate_user=True, rate_ip = True, prefix = "rate_comment_")


    @Json
    @validate(VUser(),
              VModhash(),
              VCaptcha(),
              VRatelimit(rate_user = True, rate_ip = True,
                         prefix = "rate_share_"),
              share_from = VLength('share_from', length = 100),
              emails = ValidEmails("share_to"),
              reply_to = ValidEmails("replyto", num = 1),
              message = VLength("message", length = 1000),
              thing = VByName('id'))
    def POST_share(self, res, emails, thing, share_from, reply_to,
                   message):

        # remove the ratelimit error if the user's karma is high
        sr = thing.subreddit_slow
        should_ratelimit = sr.should_ratelimit(c.user, 'link')
        if not should_ratelimit:
            c.errors.remove(errors.RATELIMIT)

        res._hide("status_" + thing._fullname)

        if res._chk_captcha(errors.BAD_CAPTCHA, thing._fullname):
            pass
        elif res._chk_error(errors.RATELIMIT, thing._fullname):
            pass
        elif (share_from is None and
              res._chk_error(errors.COMMENT_TOO_LONG,
                             'share_from_' + thing._fullname)):
            res._focus('share_from_' + thing._fullname)
        elif (message is None and
              res._chk_error(errors.COMMENT_TOO_LONG,
                             'message_' + thing._fullname)):
            res._focus('message_' + thing._fullname)
        elif not emails and res._chk_errors((errors.BAD_EMAILS,
                                             errors.NO_EMAILS,
                                             errors.TOO_MANY_EMAILS),
                                            "emails_" + thing._fullname):
            res._focus("emails_" + thing._fullname)
        elif not reply_to and res._chk_error(errors.BAD_EMAILS,
                                             "replyto_" + thing._fullname):
            res._focus("replyto_" + thing._fullname)
        else:
            c.user.add_share_emails(emails)
            c.user._commit()

            res._update("share_li_" + thing._fullname,
                        innerHTML=_('Shared'))

            res._update("sharelink_" + thing._fullname,
                        innerHTML=("<div class='clearleft'></div><p class='error'>%s</p>" %
                                   _("Your link has been shared.")))

            emailer.share(thing, emails, from_name = share_from or "",
                          body = message or "", reply_to = reply_to or "")

            #set the ratelimiter
            if should_ratelimit:
                VRatelimit.ratelimit(rate_user=True, rate_ip = True, prefix = "rate_share_")



    @Json
    @validate(VUser(),
              VModhash(),
              vote_type = VVotehash(('vh', 'id')),
              ip = ValidIP(),
              dir = VInt('dir', min=-1, max=1),
              thing = VByName('id'))
    def POST_vote(self, res, dir, thing, ip, vote_type):
        ip = request.ip
        user = c.user
        spam = (c.user._spam or
                errors.BANNED_IP in c.errors or
                errors.CHEATER in c.errors)
        dir = (True if dir > 0
               else False if dir < 0
               else None)

        isRetracted = thing.retracted if thing and isinstance(thing,Comment) else False

        # Ensure authors can't vote on their own posts / comments
        # Cannot vote on retracted comments
        if thing and thing.author_id != c.user._id and not isRetracted:
            try:
                organic = vote_type == 'organic'
                v = Vote.vote(user, thing, dir, ip, spam, organic)

                #update relevant caches
                if isinstance(thing, Link):
                    sr = thing.subreddit_slow
                    set_last_modified(c.user, 'liked')
                    set_last_modified(c.user, 'disliked')

                    if v.valid_thing:
                        expire_hot(sr)

                    if g.write_query_queue:
                        queries.new_vote(v)

                # flag search indexer that something has changed
                tc.changed(thing)

            except NotEnoughKarma, e:
                # User is downvoting and does not have enough karma.
                res._update('status_'+thing._fullname, innerHTML = e.message)
                res._show('status_'+thing._fullname)
    
    @Json
    @validate(VUser(), VModhash(),
              comment = VCommentFullName('owner_thing'),
              anonymous = VBoolean('anonymous'))
    def POST_submitballot(self, res, comment, anonymous):
        ip = request.ip
        user = c.user
        spam = (c.user._spam or
                errors.BANNED_IP in c.errors or
                errors.CHEATER in c.errors)

        if not comment:
            return

        if c.user.safe_karma < g.karma_to_vote:
            res._set_error(errors.BAD_POLL_BALLOT, comment._fullname,
                           'You do not have the required {0} karma to vote'.format(g.karma_to_vote))
            return

        any_submitted = False

        #Save a ballot for each poll answered (corresponding to POST parameters named poll_[id36])
        for param in request.POST:
            ballotparam = re.match("poll_([a-z0-9]+)", param)
            if(ballotparam and request.POST[param]):
                pollid = int(ballotparam.group(1), 36)
                pollobj = Poll._byID(pollid, data = True)
                try:
                    response = pollobj.validate_response(request.POST[param])
                    ballot = Ballot.submitballot(user, comment, pollobj, response, anonymous, ip, spam)
                except PollError as ex:
                    res._set_error(errors.BAD_POLL_BALLOT, comment._fullname, ex.message)
                else:
                    any_submitted = True
                    if g.write_query_queue:
                        queries.new_ballot(ballot)

        if any_submitted:
            res._send_things(comment)
        else:
            res._set_error(errors.BAD_POLL_BALLOT, comment._fullname, 'No valid votes found')

        # A comment might have multiple polls, with only some of them voted on, and others
        # with errors. The above call to res._send_things causes JS to erase the error
        # message. So if there were errors, make sure they're visible.

        if res.error:
            res._update(res.error.name + '_' + comment._fullname, textContent = res.error.message)

    @Json
    @validate(thing = VCommentFullName('thing'))
    def GET_rawdata(self, response, thing):
        pollids = getpolls(thing.body)
        csv = exportvotes(pollids)
        c.response_content_type = 'text/plain'
        c.response.content = csv
        c.response.headers['Content-Disposition'] = 'attachment; filename="poll.csv"'
        return c.response
    
    @Json
    @validate(VUser(),
              VModhash(),
              stylesheet_contents = nop('stylesheet_contents'),
              op = VOneOf('op',['save','preview']))
    def POST_subreddit_stylesheet(self, res, stylesheet_contents = '', op='save'):
        if not c.site.can_change_stylesheet(c.user):
            return self.abort(403,'forbidden')

        if g.css_killswitch:
            return self.abort(403,'forbidden')

        parsed, report = cssfilter.validate_css(stylesheet_contents)

        if report.errors:
            error_items = [ CssError(x).render(style='html')
                            for x in sorted(report.errors) ]

            res._update('status', innerHTML = _('Validation errors'))
            res._update('validation-errors', innerHTML = ''.join(error_items))
            res._show('error-header')
        else:
            res._hide('error-header')
            res._update('status', innerHTML = '')
            res._update('validation-errors', innerHTML = '')

        stylesheet_contents_parsed = parsed.cssText if parsed else ''
        # if the css parsed, we're going to apply it (both preview & save)
        if not report.errors:
            res._call('applyStylesheet("%s"); '  %
                      stylesheet_contents_parsed.replace('"', r"\"").replace("\n", r"\n").replace("\r", r"\r"))
        if not report.errors and op == 'save':
            stylesheet_contents_user   = stylesheet_contents

            c.site.stylesheet_contents      = stylesheet_contents_parsed
            c.site.stylesheet_contents_user = stylesheet_contents_user

            c.site.stylesheet_hash = md5(stylesheet_contents_parsed).hexdigest()

            set_last_modified(c.site,'stylesheet_contents')
            tc.changed(c.site)
            c.site._commit()

            res._update('status', innerHTML = 'saved')
            res._update('validation-errors', innerHTML = '')

        elif op == 'preview':
            # try to find a link to use, otherwise give up and
            # return
            links = cssfilter.find_preview_links(c.site)
            if not links:
                # we're probably not going to be able to find any
                # comments, either; screw it
                return

            res._show('preview-table')

            # do a regular link
            cssfilter.rendered_link('preview_link_normal',
                                    res, links,
                                    media = 'off', compress=False)
            # now do one with media
            cssfilter.rendered_link('preview_link_media',
                                    res, links,
                                    media = 'on', compress=False)
            # do a compressed link
            cssfilter.rendered_link('preview_link_compressed',
                                    res, links,
                                    media = 'off', compress=True)
            # and do a comment
            comments = cssfilter.find_preview_comments(c.site)
            if not comments:
                return
            cssfilter.rendered_comment('preview_comment',res,comments)

    @Json
    @validate(VSrModerator(),
              VModhash(),
              name = VCssName('img_name'))
    def POST_delete_sr_img(self, res, name):
        """
        Called called upon requested delete on /about/stylesheet.
        Updates the site's image list, and causes the <li> which wraps
        the image to be hidden.
        """
        # just in case we need to kill this feature from XSS
        if g.css_killswitch:
            return self.abort(403,'forbidden')
        c.site.del_image(name)
        c.site._commit()
        # hide the image and it's container
        res._hide("img-li_%s" % name)
        # reset the status
        res._update('img-status', innerHTML = _("Deleted"))


    @Json
    @validate(VModhash(),
              link = VLink('article_id'),
              name = VCssName('img_name'))
    def POST_delete_link_img(self, res, link, name):
        """
        Updates the link's image list, and causes the <li> which wraps
        the image to be hidden.
        """
        # just in case we need to kill this feature from XSS
        if g.css_killswitch:
            return self.abort(403,'forbidden')
        link.del_image(name)
        link._commit()
        # hide the image and it's container
        res._hide("img-li_%s" % name)
        # reset the status
        res._update('img-status', innerHTML = _("Deleted"))

    @Json
    @validate(VSrModerator(),
              VModhash())
    def POST_delete_sr_header(self, res):
        """
        Called when the user request that the header on a sr be reset.
        """
        # just in case we need to kill this feature from XSS
        if g.css_killswitch:
            return self.abort(403,'forbidden')
        if c.site.header:
            c.site.header = None
            c.site._commit()
        # reset the header image on the page
        res._update('header-img', src = DefaultSR.header)
        # hide the button which started this
        res._hide  ('delete-img')
        # hide the preview box
        res._hide  ('img-preview-container')
        # reset the status boxes
        res._update('img-status', innerHTML = _("Deleted"))
        res._update('status', innerHTML = "")

    def render_cached(self, cache_key, render_cls, max_age, cache_time=0, *args, **kwargs):
        """Render content using client caching and server caching."""

        # Default the cache to be the same as our max age if not
        # supplied.
        cache_time = cache_time or max_age

        # Postfix the cache key with the subreddit name
        # This scopes all the caches by subreddit
        cache_key = cache_key + '-' + c.site.name

        # Get the etag and content from the cache.
        hit = g.rendercache.get(cache_key)
        if hit:
            etag, content = hit
        else:
            # Generate and cache the content along with an etag.
            content = render_cls(*args, **kwargs).render()
            etag = '"%s"' % datetime.utcnow().isoformat()
            g.rendercache.set(cache_key, (etag, content), time=cache_time)

        # Check if the client already has the correct content and
        # throw 304 if so. Note that we want to set the max age in the
        # 304 response, we can only do this by using the
        # pylons.response object just like the etag_cache fn does
        # within pylons (it sets the etag header).  Setting it on the
        # c.response won't work as c.response isn't used when an
        # exception is thrown.  Note also that setting it on the
        # pylons.response will send the max age in the 200 response
        # (just like the etag header is sent in the response).
        response.headers['Cache-Control'] = 'max-age=%d' % max_age
        etag_cache(etag)

        # Return full response using our cached info.
        c.response.content = content
        return c.response

    TWELVE_HOURS = 3600 * 12

    def GET_side_posts(self, *a, **kw):
        """Return HTML snippet of the recent posts for the side bar."""
        # Server side cache is also invalidated when new article is posted
        return self.render_cached('side-posts', RecentArticles, g.side_posts_max_age)

    def GET_side_comments(self, *a, **kw):
        """Return HTML snippet of the recent comments for the side bar."""
        # Server side cache is also invalidated when new comment is posted
        return self.render_cached('side-comments', RecentComments, g.side_comments_max_age, self.TWELVE_HOURS)

    def GET_side_tags(self, *a, **kw):
        """Return HTML snippet of the tags for the side bar."""
        return self.render_cached('side-tags', TagCloud, g.side_tags_max_age)

    def GET_side_contributors(self, *a, **kw):
        """Return HTML snippet of the top contributors for the side bar."""
        return self.render_cached('side-contributors', TopContributors, g.side_contributors_max_age)

    def GET_side_meetups(self, *a, **kw):
        """Return HTML snippet of the upcoming meetups for the side bar."""
        ip = remote_addr(c.environ)
        location = Meetup.geoLocateIp(ip)
        # Key to group cached meetup pages with
        invalidating_key = g.rendercache.get_key_group_value(Meetup.group_cache_key())
        cache_key = "%s-side-meetups-%s" % (invalidating_key,ip)
        return self.render_cached(cache_key, UpcomingMeetups, g.side_meetups_max_age, 
                                  cache_time=self.TWELVE_HOURS, location=location, 
                                  max_distance=g.meetups_radius)

    def GET_side_monthly_contributors(self, *a, **kw):
        """Return HTML snippet of the top monthly contributors for the side bar."""
        return self.render_cached('side-monthly-contributors', TopMonthlyContributors, g.side_contributors_max_age)

    def GET_upload_sr_img(self, *a, **kw):
        """
        Completely unnecessary method which exists because safari can
        be dumb too.  On page reload after an image has been posted in
        safari, the iframe to which the request posted preserves the
        URL of the POST, and safari attempts to execute a GET against
        it.  The iframe is hidden, so what it returns is completely
        irrelevant.
        """
        return "nothing to see here."

    def GET_upload_link_img(self, *a, **kw):
        """
        As above
        """
        return "nothing to see here."

    def GET_front_recent_posts(self, *a, **kw):
        """Return HTML snippet of the recent promoted posts for the front page."""
        # Server side cache is also invalidated when new article is posted
        return self.render_cached('recent-promoted', RecentPromotedArticles, g.side_posts_max_age)

    def GET_front_meetups_map(self, *a, **kw):
        ip = remote_addr(c.environ)
        location = Meetup.geoLocateIp(ip)
        invalidating_key = g.rendercache.get_key_group_value(Meetup.group_cache_key())
        cache_key = "%s-front-meetups-%s" % (invalidating_key,ip)
        return self.render_cached(cache_key, MeetupsMap, g.side_meetups_max_age, 
                                  cache_time=self.TWELVE_HOURS, location=location, 
                                  max_distance=g.meetups_radius)

    @validate(link = VLink('article_id', redirect=False))
    def GET_article_navigation(self, link, *a, **kw):
      """Returns the article navigation fragment for the article specified"""
      author = Account._byID(link.author_id, data=True) if link else None
      return self.render_cached(
        'article_navigation_%s' % (link._id36 if link else None),
        ArticleNavigation, g.article_navigation_max_age,
        link=link, author=author
      )

    @validate(VModhash(),
              file = VLength('file', length=1024*500),
              name = VCssName("name"),
              header = nop('header'))
    def POST_upload_sr_img(self, file, header, name):
        """
        Called on /about/stylesheet when an image needs to be replaced
        or uploaded, as well as on /about/edit for updating the
        header.  Unlike every other POST in this controller, this
        method does not get called with Ajax but rather is from the
        original form POSTing to a hidden iFrame.  Unfortunately, this
        means the response needs to generate an page with a script tag
        to fire the requisite updates to the parent document, and,
        more importantly, that we can't use our normal toolkit for
        passing those responses back.

        The result of this function is a rendered UploadedImage()
        object in charge of firing the completedUploadImage() call in
        JS.
        """

        # default error list (default values will reset the errors in
        # the response if no error is raised)
        errors = dict(BAD_CSS_NAME = "", IMAGE_ERROR = "")
        try:
            cleaned = cssfilter.clean_image(file,'PNG')
            if header:
                num = None # there is one and only header, and it is unnumbered
            elif not name:
                # error if the name wasn't specified or didn't satisfy
                # the validator
                errors['BAD_CSS_NAME'] = _("Bad image name")
            else:
                num = c.site.add_image(name, max_num = g.max_sr_images)
                c.site._commit()

        except cssfilter.BadImage:
            # if the image doesn't clean up nicely, abort
            errors["IMAGE_ERROR"] = _("Bad image")
        except ValueError:
            # the add_image method will raise only on too many images
            errors['IMAGE_ERROR'] = (
                _("Too many images (you only get %d)") % g.max_sr_images)

        if any(errors.values()):
            return  UploadedImage("", "", "", errors = errors).render()
        else:
            # with the image num, save the image an upload to s3.  the
            # header image will be of the form "${c.site._fullname}.png"
            # while any other image will be ${c.site._fullname}_${num}.png
            new_url = cssfilter.save_sr_image(c.site, cleaned, num = num)
            if header:
                c.site.header = new_url
                c.site._commit()

            return UploadedImage(_('Saved'), new_url, name,
                                 errors = errors).render()


    @validate(VModhash(),
              link = VLink('article_id'),
              file = VLength('file', length=1024*500),
              name = VCssName("name"))
    def POST_upload_link_img(self, link, file, name):
        """
        Upload an image to a link

        The result of this function is a rendered UploadedImage()
        object in charge of firing the completedUploadImage() call in
        JS.
        """

        # default error list (default values will reset the errors in
        # the response if no error is raised)
        errors = dict(BAD_CSS_NAME = "", IMAGE_ERROR = "")
        try:
            cleaned = cssfilter.clean_image(file,'PNG')
            if not name:
                # error if the name wasn't specified or didn't satisfy
                # the validator
                errors['BAD_CSS_NAME'] = _("Bad image name")
            else:
                num = link.add_image(name, max_num = g.max_sr_images)
                link._commit()

        except cssfilter.BadImage:
            # if the image doesn't clean up nicely, abort
            errors["IMAGE_ERROR"] = _("Bad image")
        except ValueError:
            # the add_image method will raise only on too many images
            errors['IMAGE_ERROR'] = (
                _("Too many images (you only get %d)") % g.max_sr_images)

        if any(errors.values()):
            return  UploadedImage("", "", "", errors = errors).render()
        else:
            # with the image num, save the image an upload to s3.  the
            #  image will be of the form ${link._fullname}_${num}.png
            # Note save_sr_image expects the first argument to be a
            # subreddit, however that argument just needs to respond to
            # fullname, which links do.
            new_url = cssfilter.save_sr_image(link, cleaned, num = num)

            return UploadedImage(_('Saved'), new_url, name,
                                 errors = errors).render()


    @Json
    @validate(VAdmin(),
              VModhash(),
              VRatelimit(rate_user = True,
                         rate_ip = True,
                         prefix = 'create_reddit_'),
              sr = VByName('sr'),
              name = VSubredditName("name"),
              title = VSubredditTitle("title"),
              domain = VCnameDomain("domain"),
              description = VSubredditDesc("description"),
              lang = VLang("lang"),
              over_18 = VBoolean('over_18'),
              show_media = VBoolean('show_media'),
              type = VOneOf('type', ('public', 'private', 'restricted')),
              default_listing = VOneOf('default_listing', ListingController.listing_names())
              )
    def POST_site_admin(self, res, name ='', sr = None, **kw):
        redir = False
        kw = dict((k, v) for k, v in kw.iteritems()
                  if k in ('name', 'title', 'domain', 'description', 'over_18',
                           'show_media', 'type', 'lang', 'default_listing',))

        #if a user is banned, return rate-limit errors
        if c.user._spam:
            time = timeuntil(datetime.now(g.tz) + timedelta(seconds=600))
            c.errors.add(errors.RATELIMIT, {'time': time})

        domain = kw['domain']
        cname_sr = domain and Subreddit._by_domain(domain)
        if cname_sr and (not sr or sr != cname_sr):
                c.errors.add(errors.USED_CNAME)

        if not sr and res._chk_error(errors.RATELIMIT):
            pass
        elif not sr and res._chk_errors((errors.SUBREDDIT_EXISTS,
                                         errors.BAD_SR_NAME)):
            res._hide('example_name')
            res._focus('name')
        elif res._chk_errors((errors.NO_TITLE, errors.TITLE_TOO_LONG)):
            res._hide('example_title')
            res._focus('title')
        elif res._chk_error(errors.INVALID_OPTION):
            pass
        elif res._chk_errors((errors.BAD_CNAME, errors.USED_CNAME)):
            res._hide('example_domain')
            res._focus('domain')
        elif res._chk_error(errors.DESC_TOO_LONG):
            res._focus('description')

        res._update('status', innerHTML = '')

        if res.error:
            pass

        #creating a new reddit
        elif not sr:
            sr = Subreddit._create_and_subscribe(name, c.user, kw)

        #editting an existing reddit
        elif sr.is_moderator(c.user) or c.user_is_admin:
            #assume sr existed, or was just built
            clear_memo('subreddit._by_domain',
                       Subreddit, _force_unicode(sr.domain))
            for k, v in kw.iteritems():
                setattr(sr, k, v)
            sr._commit()
            clear_memo('subreddit._by_domain',
                       Subreddit, _force_unicode(sr.domain))

            # flag search indexer that something has changed
            tc.changed(sr)

            res._update('status', innerHTML = _('Saved'))


        if redir:
            res._redirect(redir)

    @Json
    @validate(VModhash(),
              VSrCanBan('id'),
              thing = VByName('id'))
    def POST_ban(self, res, thing):
        thing.moderator_banned = not c.user_is_admin
        thing.banner = c.user.name
        thing._commit()
        # NB: change table updated by reporting
        unreport(thing, correct=True, auto=False)

    @Json
    @validate(VModhash(),
              VSrCanBan('id'),
              thing = VByName('id'))
    def POST_unban(self, res, thing):
        # NB: change table updated by reporting
        unreport(thing, correct=False)

    @Json
    @validate(VModhash(),
              VSrCanBan('id'),
              thing = VByName('id'))
    def POST_ignore(self, res, thing):
        # NB: change table updated by reporting
        unreport(thing, correct=False)

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByName('id'))
    def POST_save(self, res, thing):
        r = thing._save(c.user)
        if g.write_query_queue:
            queries.new_savehide(r)

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByName('id'))
    def POST_unsave(self, res, thing):
        r = thing._unsave(c.user)
        if g.write_query_queue and r:
            queries.new_savehide(r)

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByName('id'))
    def POST_hide(self, res, thing):
        r = thing._hide(c.user)
        if g.write_query_queue:
            queries.new_savehide(r)

    @Json
    @validate(VUser(),
              VModhash(),
              thing = VByName('id'))
    def POST_unhide(self, res, thing):
        r = thing._unhide(c.user)
        if g.write_query_queue and r:
            queries.new_savehide(r)


    @Json
    @validate(link = VByName('link_id'),
              sort = VMenu('where', CommentSortMenu),
              children = VCommentIDs('children'),
              depth = VInt('depth', min = 0, max = 8),
              mc_id = nop('id'))
    def POST_morechildren(self, res, link, sort, children, depth, mc_id):
        if children:
            builder = CommentBuilder(link, CommentSortMenu.operator(sort), children)
            items = builder.get_items(starting_depth = depth, num = 20)
            def _children(cur_items):
                items = []
                for cm in cur_items:
                    items.append(cm)
                    if hasattr(cm, 'child'):
                        if hasattr(cm.child, 'things'):
                            items.extend(_children(cm.child.things))
                            cm.child = None
                        else:
                            items.append(cm.child)

                return items
            # assumes there is at least one child
#            a = _children(items[0].child.things)
            a = []
            for item in items:
                a.append(item)
                if hasattr(item, 'child'):
                    a.extend(_children(item.child.things))
                    item.child = None

            # the result is not always sufficient to replace the
            # morechildren link
            if mc_id not in [x._fullname for x in a]:
                res._hide('thingrow_' + str(mc_id))
            res._send_things(a)


    @validate(uh = nop('uh'),
              action = VOneOf('what', ('like', 'dislike', 'save')),
              links = VUrl(['u']))
    def GET_bookmarklet(self, action, uh, links):
        '''Controller for the functionality of the bookmarklets (not the distribution page)'''

        # the redirect handler will clobber the extension if not told otherwise
        c.extension = "png"

        if not c.user_is_loggedin:
            return self.redirect("/static/css_login.png")
        # check the modhash (or force them to get new bookmarlets)
        elif not c.user.valid_hash(uh) or not action:
            return self.redirect("/static/css_update.png")
        # unlike most cases, if not already submitted, error.
        elif errors.ALREADY_SUB in c.errors:
            # preserve the subreddit if not Default
            sr = c.site if not isinstance(c.site, FakeSubreddit) else None

            # check permissions on those links to make sure votes will count
            Subreddit.load_subreddits(links, return_dict = False)
            user = c.user if c.user_is_loggedin else None
            links = [l for l in links if l.subreddit_slow.can_view(user)]

            if links:
                if action in ['like', 'dislike']:
                    #vote up all of the links
                    for link in links:
                        v = Vote.vote(c.user, link, action == 'like', request.ip)
                        if g.write_query_queue:
                            queries.new_vote(v)
                elif action == 'save':
                    link = max(links, key = lambda x: x._score)
                    r = link._save(c.user)
                    if g.write_query_queue:
                        queries.new_savehide(r)
                return self.redirect("/static/css_%sd.png" % action)
        return self.redirect("/static/css_submit.png")


    @Json
    @validate(user = VUserWithEmail('name'))
    def POST_password(self, res, user):
        res._update('status', innerHTML = '')
        if res._chk_error(errors.USER_DOESNT_EXIST):
            res._focus('name')
        elif res._chk_error(errors.NO_EMAIL_FOR_USER):
            res._focus('name')
        else:
            emailer.password_email(user)
            res._success()

    @Json
    @validate(user = VCacheKey('reset', ('key', 'name')),
              key= nop('key'),
              password = VPassword(['passwd', 'passwd2']))
    def POST_resetpassword(self, res, user, key, password):
        res._update('status', innerHTML = '')
        if res._chk_error(errors.BAD_PASSWORD):
            res._focus('passwd')
        elif res._chk_error(errors.BAD_PASSWORD_MATCH):
            res._focus('passwd2')
        elif errors.BAD_USERNAME in c.errors:
            cache.delete(str('reset_%s' % key))
            return res._redirect('/password')
        elif user:
            cache.delete(str('reset_%s' % key))
            change_password(user, password)
            self._login(res, user, '/resetpassword')


    @Json
    @validate(VUser())
    def POST_frame(self, res):
        c.user.pref_frame = True
        c.user._commit()


    @Json
    @validate(VUser())
    def POST_noframe(self, res):
        c.user.pref_frame = False
        c.user._commit()


    @Json
    @validate(VUser(),
              where=nop('where'),
              sort = nop('sort'))
    def POST_sort(self, res, where, sort):
        if where.startswith('sort_'):
            setattr(c.user, where, sort)
        c.user._commit()

    @Json
    def POST_new_captcha(self, res, *a, **kw):
        res.captcha = dict(iden = get_iden(), refresh = True)

    @Json
    @validate(VAdmin(),
              l = nop('id'))
    def POST_deltranslator(self, res, l):
        lang, a = l.split('_')
        if a and Translator.exists(lang):
            tr = Translator(locale = lang)
            tr.author.remove(a)
            tr.save()


    @Json
    @validate(VUser(),
              VModhash(),
              action = VOneOf('action', ('sub', 'unsub')),
              sr = VByName('sr'))
    def POST_subscribe(self, res, action, sr):
        self._subscribe(sr, action == 'sub')

    def _subscribe(self, sr, sub):
        Subreddit.subscribe_defaults(c.user)

        if sub:
            if sr.add_subscriber(c.user):
                sr._incr('_ups', 1)
        else:
            if sr.remove_subscriber(c.user):
                sr._incr('_ups', -1)
        tc.changed(sr)


    @Json
    @validate(VAdmin(),
              lang = nop("id"))
    def POST_disable_lang(self, res, lang):
        if lang and Translator.exists(lang):
            tr = Translator(locale = lang)
            tr._is_enabled = False


    @Json
    @validate(VAdmin(),
              lang = nop("id"))
    def POST_enable_lang(self, res, lang):
        if lang and Translator.exists(lang):
            tr = Translator(locale = lang)
            tr._is_enabled = True

    def action_cookie(action):
        s = action + request.ip + request.user_agent
        return hashlib.sha1(s).hexdigest()


    @Json
    @validate(num_margin = VCssMeasure('num_margin'),
              mid_margin = VCssMeasure('mid_margin'),
              links = VFullNames('links'))
    def POST_fetch_links(self, res, num_margin, mid_margin, links):
        b = IDBuilder([l._fullname for l in links],
                      wrap = ListingController.builder_wrapper)
        l = OrganicListing(b)
        l.num_margin = num_margin
        l.mid_margin = mid_margin
        res.object = res._thing(l.listing(), action = 'populate')

    @Json
    @validate(VUser(),
              ui_elem = VOneOf('id', ('organic',)))
    def POST_disable_ui(self, res, ui_elem):
        if ui_elem:
            pref = "pref_%s" % ui_elem
            if getattr(c.user, pref):
                setattr(c.user, "pref_" + ui_elem, False)
                c.user._commit()

    @Json
    @validate(VSponsor(),
              thing = VByName('id'))
    def POST_promote(self, res, thing):
        promote(thing)

    @Json
    @validate(VSponsor(),
              thing = VByName('id'))
    def POST_unpromote(self, res, thing):
        unpromote(thing)

    @Json
    @validate(VSponsor(),
              ValidDomain('url'),
              ip               = ValidIP(),
              l                = VLink('link_id'),
              title            = VTitle('title'),
              url              = VUrl(['url', 'sr']),
              sr               = VSubmitSR('sr'),
              subscribers_only = VBoolean('subscribers_only'),
              disable_comments = VBoolean('disable_comments'),
              expire           = VOneOf('expire', ['nomodify', 'expirein', 'cancel']),
              timelimitlength  = VInt('timelimitlength',1,1000),
              timelimittype    = VOneOf('timelimittype',['hours','days','weeks']))
    def POST_edit_promo(self, res, ip,
                        title, url, sr, subscribers_only,
                        disable_comments,
                        expire = None, timelimitlength = None, timelimittype = None,
                        l = None):
        res._update('status', innerHTML = '')
        if isinstance(url, str):
            # VUrl may have modified the URL to make it valid, like
            # adding http://
            res._update('url', value=url)
        elif isinstance(url, tuple) and isinstance(url[0], Link):
            # there's already one or more links with this URL, but
            # we're allowing mutliple submissions, so we really just
            # want the URL
            url = url[0].url

        if res._chk_error(errors.NO_TITLE):
            res._focus('title')
        elif res._chk_errors((errors.NO_URL,errors.BAD_URL)):
            res._focus('url')
        elif (not l or url != l.url) and res._chk_error(errors.ALREADY_SUB):
            #if url == l.url, we're just editting something else
            res._focus('url')
        elif res._chk_error(errors.SUBREDDIT_NOEXIST) or res._chk_error(errors.SUBREDDIT_FORBIDDEN):
            res._focus('sr')
        elif expire == 'expirein' and res._chk_error(errors.BAD_NUMBER):
            res._focus('timelimitlength')
        elif l:
            l.title = title
            old_url = l.url
            l.url = url

            l.promoted_subscribersonly = subscribers_only
            l.disable_comments = disable_comments

            if expire == 'cancel':
                l.promote_until = None
            elif expire == 'expirein' and timelimitlength and timelimittype:
                l.promote_until = timefromnow("%d %s" % (timelimitlength, timelimittype))

            l._commit()
            l.update_url_cache(old_url)

            res._redirect('/promote/edit_promo/%s' % to36(l._id))
        else:
            l = Link._submit(title, url, c.user, sr, ip, False)

            if expire == 'expirein' and timelimitlength and timelimittype:
                promote_until = timefromnow("%d %s" % (timelimitlength, timelimittype))
            else:
                promote_until = None

            promote(l, subscribers_only = subscribers_only,
                    promote_until = promote_until,
                    disable_comments = disable_comments)

            res._redirect('/promote/edit_promo/%s' % to36(l._id))

    def GET_link_thumb(self, *a, **kw):
        """
        See GET_upload_sr_image for rationale
        """
        return "nothing to see here."

    @validate(VSponsor(),
              link = VByName('link_id'),
              file = VLength('file',500*1024))
    def POST_link_thumb(self, link=None, file=None):
        errors = dict(BAD_CSS_NAME = "", IMAGE_ERROR = "")

        try:
            force_thumbnail(link, file)
        except cssfilter.BadImage:
            # if the image doesn't clean up nicely, abort
            errors["IMAGE_ERROR"] = _("Bad image")

        if any(errors.values()):
            return  UploadedImage("", "", "upload", errors = errors).render()
        else:
            return UploadedImage(_('Saved'), thumbnail_url(link), "upload",
                                 errors = errors).render()


    @Json
    @validate(ids = VLinkFullnames('ids'))
    def POST_onload(self, res, ids, *a, **kw):
        if not ids:
            res.object = {}
            return

        links = {}

        # make sure that they are really promoted
        promoted = Link._by_fullname(ids, data = True, return_dict = False)
        promoted = [ l for l in promoted if l.promoted ]

        for l in promoted:
            links[l._fullname] = [
                tracking.PromotedLinkInfo.gen_url(fullname=l._fullname,
                                                  ip = request.ip),
                tracking.PromotedLinkClickInfo.gen_url(fullname = l._fullname,
                                                       dest = l.url,
                                                       ip = request.ip)
                ]
        res.object = links

