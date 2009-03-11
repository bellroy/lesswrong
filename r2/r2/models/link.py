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
from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, \
     CreationError
from r2.lib.utils import base_url, tup, domain, worker, title_to_url, UrlParser
from account import Account
from subreddit import Subreddit
from printable import Printable
from r2.config import cache
from r2.lib.memoize import memoize, clear_memo
from r2.lib import utils
from mako.filters import url_escape
from r2.lib.strings import strings, Score
from r2.lib.db.operators import lower
from r2.lib.filters import _force_unicode

from pylons import c, g, request
from pylons.i18n import ungettext

import re
import random
import urllib
from datetime import datetime

class LinkExists(Exception): pass

# defining types
class Link(Thing, Printable):
    _data_int_props = Thing._data_int_props + ('num_comments', 'reported')
    _defaults = dict(is_self = False,
                     reported = 0, num_comments = 0,
                     moderator_banned = False,
                     banned_before_moderator = False,
                     media_object = None,
                     has_thumbnail = False,
                     promoted = False,
                     promoted_subscribersonly = False,
                     promote_until = None,
                     promoted_by = None,
                     disable_comments = False,
                     ip = '0.0.0.0',
                     render_full = False,
                     images = None,
                     blessed = False,
                     comments_enabled = True)

    _only_whitespace = re.compile('^\s*$', re.UNICODE)
    _more_marker = '<a id="more"></a>'

    def __init__(self, *a, **kw):
        Thing.__init__(self, *a, **kw)

    @classmethod
    def by_url_key(cls, url):
        return base_url(url.lower()).encode('utf8')

    @classmethod
    def _by_url(cls, url, sr):
        from subreddit import Default
        if sr == Default:
            sr = None
            
        url = cls.by_url_key(url)
        link_ids = g.permacache.get(url)
        if link_ids:
            links = Link._byID(link_ids, data = True, return_dict = False)
            links = [l for l in links if not l._deleted]

            if links and sr:
                for link in links:
                    if sr._id == link.sr_id:
                        return link
            elif links:
                return links

        raise NotFound, 'Link "%s"' % url
        

    def can_submit(self, user):
        if c.user_is_admin:
            return True
        elif self.author_id == c.user._id:
            # They can submit if they are the author and still have access
            # to the subreddit of the article
            sr = Subreddit._byID(self.sr_id, data=True)
            return sr.can_submit(user)
        else:
            return False
            
    def is_blessed(self):
        return self.blessed

    def set_url_cache(self):
        if self.url != 'self':
            key = self.by_url_key(self.url)
            link_ids = g.permacache.get(key) or []
            if self._id not in link_ids:
                link_ids.append(self._id)
            g.permacache.set(key, link_ids)

    def update_url_cache(self, old_url):
        """Remove the old url from the by_url cache then update the
        cache with the new url."""
        if old_url != 'self':
            key = self.by_url_key(old_url)
            link_ids = g.permacache.get(key) or []
            while self._id in link_ids:
                link_ids.remove(self._id)
            g.permacache.set(key, link_ids)
        self.set_url_cache()

    @property
    def already_submitted_link(self):
        return self.make_permalink_slow() + '?already_submitted=true'

    def resubmit_link(self, sr_url = False):
        submit_url  = self.subreddit_slow.path if sr_url else '/'
        submit_url += 'submit?resubmit=true&url=' + url_escape(self.url)
        return submit_url

    @classmethod
    def _submit(cls, title, article, author, sr, ip, tags, spam = False):
        l = cls(title = title,
                url = 'self',
                _spam = spam,
                author_id = author._id,
                sr_id = sr._id, 
                lang = sr.lang,
                ip = ip,
                article = article
                )
        l._commit()
        l.set_url_cache()
        # Add tags
        for tag in tags:
            l.add_tag(tag)
        return l
        
    def _summary(self):
        if hasattr(self, 'article'):
            return self.article.split(self._more_marker)[0]
            
    def _has_more(self):
        if hasattr(self, 'article'):
            return self.article.find(self._more_marker) >= 0
            
    def _more(self):
        if hasattr(self, 'article'):
            return self.article.split(self._more_marker)[1]

    @classmethod
    def _somethinged(cls, rel, user, link, name):
        return rel._fast_query(tup(user), tup(link), name = name)

    def _something(self, rel, user, somethinged, name):
        try:
            saved = rel(user, self, name=name)
            saved._commit()
            return saved
        except CreationError, e:
            return somethinged(user, self)[(user, self, name)]

    def _unsomething(self, user, somethinged, name):
        saved = somethinged(user, self)[(user, self, name)]
        if saved:
            saved._delete()
            return saved

    @classmethod
    def _saved(cls, user, link):
        return cls._somethinged(SaveHide, user, link, 'save')

    def _save(self, user):
        return self._something(SaveHide, user, self._saved, 'save')

    def _unsave(self, user):
        return self._unsomething(user, self._saved, 'save')

    @classmethod
    def _clicked(cls, user, link):
        return cls._somethinged(Click, user, link, 'click')

    def _click(self, user):
        return self._something(Click, user, self._clicked, 'click')

    @classmethod
    def _hidden(cls, user, link):
        return cls._somethinged(SaveHide, user, link, 'hide')

    def _hide(self, user):
        return self._something(SaveHide, user, self._hidden, 'hide')

    def _unhide(self, user):
        return self._unsomething(user, self._hidden, 'hide')

    def keep_item(self, wrapped):
        user = c.user if c.user_is_loggedin else None

        if not c.user_is_admin:
            if self._spam and (not user or
                               (user and self.author_id != user._id)):
                return False
        
            #author_karma = wrapped.author.link_karma
            #if author_karma <= 0 and random.randint(author_karma, 0) != 0:
                #return False

        if user:
            if user.pref_hide_ups and wrapped.likes == True:
                return False
        
            if user.pref_hide_downs and wrapped.likes == False:
                return False

            if wrapped._score < user.pref_min_link_score:
                return False

            if wrapped.hidden:
                return False

        return True

    @staticmethod
    def cache_key(wrapped):
        if c.user_is_admin:
            return False

        s = (str(i) for i in (wrapped.render_class.__name__,
                              wrapped._fullname,
                              bool(c.user_is_sponsor),
                              bool(c.user_is_loggedin),
                              wrapped.subreddit == c.site,
                              c.user.pref_newwindow,
                              c.user.pref_frame,
                              c.user.pref_compress,
                              c.user.pref_media,
                              request.host,
                              c.cname, 
                              wrapped.author == c.user,
                              wrapped.likes,
                              wrapped.saved,
                              wrapped.clicked,
                              wrapped.hidden,
                              wrapped.friend,
                              wrapped.show_spam,
                              wrapped.show_reports,
                              wrapped.can_ban,
                              wrapped.thumbnail,
                              wrapped.moderator_banned,
                              wrapped.render_full,
                              wrapped.comments_enabled))
        # htmllite depends on other get params
        s = ''.join(s)
        if c.render_style == "htmllite":
            s += ''.join(map(str, [request.get.has_key('style'),
                                   request.get.has_key('expanded'),
                                   request.get.has_key('twocolumn'),
                                   c.bgcolor,
                                   c.bordercolor]))
        return s

    def make_permalink(self, sr, force_domain = False):
        from r2.lib.template_helpers import get_domain
        p = "lw/%s/%s/" % (self._id36, title_to_url(self.title))
        if c.default_sr:
            res = "/%s" % p
        elif not c.cname:
            res = "/r/%s/%s" % (sr.name, p)
        elif sr != c.site or force_domain:
            res = "http://%s/%s" % (get_domain(cname = (c.cname and sr == c.site),
                                               subreddit = not c.cname), p)
        else:
            res = "/%s" % p
        return res

    def make_permalink_slow(self):
        return self.make_permalink(self.subreddit_slow)
    
    @property
    def canonical_url(self):
        from r2.lib.template_helpers import get_domain
        p = "lw/%s/%s/" % (self._id36, title_to_url(self.title))
        return "http://%s/%s" % (get_domain(subreddit = False), p)

    @classmethod
    def add_props(cls, user, wrapped):
        from r2.lib.count import incr_counts
        from r2.lib.media import thumbnail_url
        from r2.lib.utils import timeago

        saved = Link._saved(user, wrapped) if user else {}
        hidden = Link._hidden(user, wrapped) if user else {}
        #clicked = Link._clicked(user, wrapped) if user else {}
        clicked = {}

        for item in wrapped:
            show_media = False
            if c.user.pref_compress:
                pass
            elif c.user.pref_media == 'on':
                show_media = True
            elif c.user.pref_media == 'subreddit' and item.subreddit.show_media:
                show_media = True
            elif (item.promoted
                  and item.has_thumbnail
                  and c.user.pref_media != 'off'):
                show_media = True

            if not show_media:
                item.thumbnail = ""
            elif item.has_thumbnail:
                item.thumbnail = thumbnail_url(item)
            else:
                item.thumbnail = g.default_thumb
            
            item.score = max(0, item.score)

            item.domain = (domain(item.url) if not item.is_self
                          else 'self.' + item.subreddit.name)
            if not hasattr(item,'top_link'):
                item.top_link = False
            item.urlprefix = ''
            item.saved = bool(saved.get((user, item, 'save')))
            item.hidden = bool(hidden.get((user, item, 'hide')))
            item.clicked = bool(clicked.get((user, item, 'click')))
            item.num = None
            item.score_fmt = Score.number_only
            item.permalink = item.make_permalink(item.subreddit)
            if item.is_self:
                item.url = item.make_permalink(item.subreddit, force_domain = True)

            if c.user_is_admin:
                item.hide_score = False
            elif item.promoted:
                item.hide_score = True
            elif c.user == item.author:
                item.hide_score = False
            elif item._date > timeago("2 hours"):
                item.hide_score = True
            else:
                item.hide_score = False

            if c.user_is_loggedin and item.author._id == c.user._id:
                item.nofollow = False
            elif item.score <= 1 or item._spam or item.author._spam:
                item.nofollow = True
            else:
                item.nofollow = False

        if c.user_is_loggedin:
            incr_counts(wrapped)

    @property
    def subreddit_slow(self):
        from subreddit import Subreddit
        """return's a link's subreddit. in most case the subreddit is already
        on the wrapped link (as .subreddit), and that should be used
        when possible. """
        return Subreddit._byID(self.sr_id, True, return_dict = False)

    def change_subreddit(self, new_sr_id):
        """Change the subreddit of the link and update its date"""
        if self.sr_id != new_sr_id:
            self.sr_id = new_sr_id
            self._date = datetime.now(g.tz)
            self._commit()

    def set_blessed(self, is_blessed):
        if self.blessed != is_blessed:
          self.blessed = is_blessed
          self.date = datetime.now(g.tz)
          self._commit()

    def get_images(self):
        """
        Iterator over list of (name, image_num) pairs which have been
        uploaded for custom styling of this subreddit.
        """
        if self.images:
          for name, img_num in self.images.iteritems():
              if isinstance(img_num, int):
                  yield (name, img_num)

    def add_image(self, name, max_num = None):
        """
        Adds an image to the link's image list.  The resulting
        number of the image is returned.  Note that image numbers are
        non-sequential insofar as unused numbers in an existing range
        will be populated before a number outside the range is
        returned.  Imaged deleted with del_image are pushed onto the
        "/empties/" stack in the images dict, and those values are
        pop'd until the stack is empty.

        raises ValueError if the resulting number is >= max_num.

        The Link will be _dirty if a new image has been added to
        its images list, and no _commit is called.
        """
        if not self.images:
          self.images = {}
          
        if not self.images.has_key(name):
            # copy and blank out the images list to flag as _dirty
            l = self.images
            self.images = None
            # initialize the /empties/ list
            l.setdefault('/empties/', [])
            try:
                num = l['/empties/'].pop() # grab old number if we can
            except IndexError:
                num = len(l) - 1 # one less to account for /empties/ key
            if max_num is not None and num >= max_num:
                raise ValueError, "too many images"
            # update the dictionary and rewrite to images attr
            l[name] = num
            self.images = l
        else:
            # we've seen the image before, so just return the existing num
            num = self.images[name]
        return num

    def del_image(self, name):
        """
        Deletes an image from the images dictionary assuming an image
        of that name is in the current dictionary.  The freed up
        number is pushed onto the /empties/ stack for later recycling
        by add_image.

        The Subreddit will be _dirty if image has been removed from
        its images list, and no _commit is called.
        """
        if not self.images:
          return

        if self.images.has_key(name):
            l = self.images
            self.images = None
            l.setdefault('/empties/', [])
            # push the number on the empties list
            l['/empties/'].append(l[name])
            del l[name]
            self.images = l


    def add_tag(self, tag_name, name = 'tag'):
        """Adds a tag of the given name to the link. If the tag does not
           exist it is created"""
        if self._only_whitespace.match(tag_name):
            # Don't allow an empty tag
            return

        try:
            tag = Tag._by_name(tag_name)
        except NotFound:
            tag = Tag._new(tag_name)
            tag._commit()

        # See if link already has this tag
        tags = LinkTag._fast_query(tup(self), tup(tag), name=name)
        link_tag = tags[(self, tag, name)]
        if not link_tag:
            link_tag = LinkTag(self, tag, name=name)
            link_tag._commit()

        return link_tag

    def remove_tag(self, tag_name, name='tag'):
        """Removes a tag from the link. The tag is not deleted,
           just the relationship between the link and the tag"""
        try:
            tag = Tag._by_name(tag_name)
        except NotFound:
            return False

        tags = LinkTag._fast_query(tup(self), tup(tag), name=name)
        link_tag = tags[(self, tag, name)]
        if link_tag:
            link_tag._delete()
            return link_tag

    def get_tags(self):
        q = LinkTag._query(LinkTag.c._thing1_id == self._id,
                           LinkTag.c._name == 'tag',
                           LinkTag.c._t2_deleted == False,
                           eager_load = True,
                           thing_data = not g.use_query_cache
                      )
        return [link_tag._thing2 for link_tag in q]

    def set_tags(self, tags):
        """Adds and/or removes tags to match the list given"""
        current_tags = set(self.tag_names())
        updated_tags = set(tags)
        removed_tags = current_tags.difference(updated_tags)
        new_tags = updated_tags.difference(current_tags)
        
        for tag in new_tags:
            self.add_tag(tag)
        
        for tag in removed_tags:
            self.remove_tag(tag)
        
    def tag_names(self):
        """Returns just the names of the tags of this article"""
        return [tag.name for tag in self.get_tags()]

# Note that there are no instances of PromotedLink or LinkCompressed,
# so overriding their methods here will not change their behaviour
# (except for add_props). These classes are used to override the
# render_class on a Wrapped to change the template used for rendering

class PromotedLink(Link):
    _nodb = True

    @classmethod
    def add_props(cls, user, wrapped):
        Link.add_props(user, wrapped)

        try:
            if c.user_is_sponsor:
                promoted_by_ids = set(x.promoted_by
                                      for x in wrapped
                                      if hasattr(x,'promoted_by'))
                promoted_by_accounts = Account._byID(promoted_by_ids,
                                                     data=True)
            else:
                promoted_by_accounts = {}

        except NotFound:
            # since this is just cosmetic, we can skip it altogether
            # if one isn't found or is broken
            promoted_by_accounts = {}

        for item in wrapped:
            # these are potentially paid for placement
            item.nofollow = True
            if item.promoted_by in promoted_by_accounts:
                item.promoted_by_name = promoted_by_accounts[item.promoted_by].name
            else:
                # keep the template from trying to read it
                item.promoted_by = None

class LinkCompressed(Link):
    _nodb = True

    @classmethod
    def add_props(cls, user, wrapped):
        Link.add_props(user, wrapped)

        for item in wrapped:
            item.score_fmt = Score.points


class InlineArticle(Link):
    """Exists to gain a different render_class in Wrapped"""
    _nodb = True


class TagExists(Exception): pass

class Tag(Thing):
    """A tag on a link/article"""
    @classmethod
    def _new(self, name, **kw):
        tag_name = name.lower()
        try:
            tag = Tag._by_name(tag_name)
            raise TagExists
        except NotFound:
            tag = Tag(name = tag_name, **kw)
            tag._commit()
            clear_memo('tag._by_name', Tag, name.lower())
            return tag

    @classmethod
    @memoize('tag._by_name')
    def _by_name_cache(cls, name):
        q = cls._query(lower(cls.c.name) == name.lower(), limit = 1)
        l = list(q)
        if l:
            return l[0]._id

    @classmethod
    def _by_name(cls, name):
        #lower name here so there is only one cache
        name = name.lower()

        tag_id = cls._by_name_cache(name)
        if tag_id:
            return cls._byID(tag_id, True)
        else:
            raise NotFound, 'Tag %s' % name

    @property
    def path(self):
        """Returns the path to the tag listing for this tag"""
        quoted_tag_name = urllib.quote(self.name.encode('utf8'))
        if not c.default_sr:
            return "/r/%s/tag/%s/" % (c.site.name, quoted_tag_name)
        else:
            return "/tag/%s/" % (quoted_tag_name)

    @classmethod
    # @memoize('tag.tag_cloud_for_subreddits') enable when it is cleared at appropiate points
    def tag_cloud_for_subreddits(cls, sr_ids):
        from r2.lib.db import tdb_sql as tdb
        import sqlalchemy as sa

        type = tdb.rel_types_id[LinkTag._type_id]
        linktag_thing_table = type.rel_table[0]

        link_type = tdb.types_id[Link._type_id]
        link_data_table = link_type.data_table[0]
        link_thing_table = link_type.thing_table

        link_sr = sa.select([
            link_data_table.c.thing_id,
            sa.cast(link_data_table.c.value, sa.INT).label('sr_id')],
            link_data_table.c.key == 'sr_id').alias('link_sr')

        query = sa.select([linktag_thing_table.c.thing2_id,
                          sa.func.count(linktag_thing_table.c.thing1_id)],
                          sa.and_(linktag_thing_table.c.thing1_id == link_sr.c.thing_id,
                                  linktag_thing_table.c.thing1_id == link_thing_table.c.thing_id,
                                  link_thing_table.c.spam == False,
                                  link_sr.c.sr_id.in_(*sr_ids)),
                          group_by = [linktag_thing_table.c.thing2_id],
                          having = sa.func.count(linktag_thing_table.c.thing1_id) > 1,
                          order_by = sa.desc(sa.func.count(linktag_thing_table.c.thing1_id)),
                          limit = 100)

        rows = query.execute().fetchall()
        tags = []
        for result in rows:
            tag = Tag._byID(result.thing2_id, data=True)
            tags.append((tag, result.count))

        # Order by tag name
        tags.sort(key=lambda x: _force_unicode(x[0].name))
        return cls.make_cloud(10, tags)

    @classmethod
    def make_cloud(cls, steps, input):
        # From: http://www.car-chase.net/2007/jan/16/log-based-tag-clouds-python/
        import math

        if len(input) <= 0:
          return []
        else:
            temp, newThresholds, results = [], [], []
            for item in input:
                temp.append(item[1])
            maxWeight = float(max(temp))
            minWeight = float(min(temp))
            newDelta = (maxWeight - minWeight)/float(steps)
            for i in range(steps + 1):
               newThresholds.append((100 * math.log((minWeight + i * newDelta) + 2), i))
            for tag in input:
                fontSet = False
                for threshold in newThresholds[1:int(steps)+1]:
                    if (100 * math.log(tag[1] + 2)) <= threshold[0] and not fontSet:
                        results.append(tuple([tag[0], threshold[1]]))
                        fontSet = True
            return results


class LinkTag(Relation(Link, Tag)):
    pass


class Comment(Thing, Printable):
    _data_int_props = Thing._data_int_props + ('reported',)
    _defaults = dict(reported = 0, 
                     moderator_banned = False,
                     banned_before_moderator = False)

    def _markdown(self):
        pass

    def _delete(self):
        link = Link._byID(self.link_id, data = True)
        link._incr('num_comments', -1)
    
    @classmethod
    def _new(cls, author, link, parent, body, ip, spam = False):
        c = Comment(body = body,
                    link_id = link._id,
                    sr_id = link.sr_id,
                    author_id = author._id,
                    ip = ip)

        c._spam = spam

        #these props aren't relations
        if parent:
            c.parent_id = parent._id

        c._commit()

        link._incr('num_comments', 1)

        inbox_rel = None
        if parent:
            to = Account._byID(parent.author_id)
            # only global admins can be message spammed.
            if not c._spam or to.name in g.admins:
                inbox_rel = Inbox._add(to, c, 'inbox')

        #clear that chache
        clear_memo('builder.link_comments2', link._id)

        return (c, inbox_rel)

    @property
    def subreddit_slow(self):
        from subreddit import Subreddit
        """return's a comments's subreddit. in most case the subreddit is already
        on the wrapped link (as .subreddit), and that should be used
        when possible. if sr_id does not exist, then use the parent link's"""
        self._safe_load()

        if hasattr(self, 'sr_id'):
            sr_id = self.sr_id
        else:
            l = Link._byID(self.link_id, True)
            sr_id = l.sr_id
        return Subreddit._byID(sr_id, True, return_dict = False)

    def keep_item(self, wrapped):
        return True

    @staticmethod
    def cache_key(wrapped):
        if c.user_is_admin:
            return False

        s = (str(i) for i in (c.profilepage,
                              c.full_comment_listing,
                              wrapped._fullname,
                              bool(c.user_is_loggedin),
                              c.focal_comment == wrapped._id36,
                              request.host,
                              c.cname, 
                              wrapped.author == c.user,
                              wrapped.likes,
                              wrapped.friend,
                              wrapped.collapsed,
                              wrapped.moderator_banned,
                              wrapped.show_spam,
                              wrapped.show_reports,
                              wrapped.can_ban,
                              wrapped.moderator_banned,
                              wrapped.can_reply,
                              wrapped.deleted))
        s = ''.join(s)
        return s

    def make_permalink(self, link, sr=None, context=1):
        return link.make_permalink(sr) + self._id36

    def make_anchored_permalink(self, context=1, anchor=None):
        permalink = UrlParser(self.make_permalink_slow())
        permalink.update_query(context=context)
        permalink.fragment = anchor if anchor else self._id36
        return permalink.unparse()

    def make_permalink_slow(self):
        l = Link._byID(self.link_id, data=True)
        return self.make_permalink(l, l.subreddit_slow)
    
    @classmethod
    def add_props(cls, user, wrapped):
        #fetch parent links
        links = Link._byID(set(l.link_id for l in wrapped), True)
        

        #get srs for comments that don't have them (old comments)
        for cm in wrapped:
            if not hasattr(cm, 'sr_id'):
                cm.sr_id = links[cm.link_id].sr_id
        
        subreddits = Subreddit._byID(set(cm.sr_id for cm in wrapped),
                                     data=True,return_dict=False)
        can_reply_srs = set(s._id for s in subreddits if s.can_comment(user))

        min_score = c.user.pref_min_comment_score

        cids = dict((w._id, w) for w in wrapped)

        for item in wrapped:
            item.link = links.get(item.link_id)
            if not hasattr(item, 'subreddit'):
                item.subreddit = item.subreddit_slow
            if hasattr(item, 'parent_id'):
                parent = Comment._byID(item.parent_id, True)
                parent_author = Account._byID(parent.author_id)
                item.parent_author = parent_author

                if not c.full_comment_listing and cids.has_key(item.parent_id):
                    item.parent_permalink = '#' + utils.to36(item.parent_id)
                else:
                    item.parent_permalink = parent.make_permalink(item.link, item.subreddit) + '#comments'
            else:
                item.parent_permalink = None
                item.parent_author = None

            item.can_reply = (item.sr_id in can_reply_srs)


            # not deleted on profile pages,
            # deleted if spam and not author or admin
            item.deleted = (not c.profilepage and
                           (item._deleted or
                            (item._spam and
                             item.author != c.user and
                             not item.show_spam)))

            # don't collapse for admins, on profile pages, or if deleted
            item.collapsed = ((item.score < min_score) and
                             not (c.profilepage or
                                  item.deleted or
                                  c.user_is_admin))
                
            if not hasattr(item,'editted'):
                item.editted = False
            #will get updated in builder
            item.num_children = 0
            item.score_fmt = Score.points
            item.permalink = item.make_permalink(item.link, item.subreddit)

class InlineComment(Comment):
    """Exists to gain a different render_class in Wrapped"""
    _nodb = True

class MoreComments(object):
    show_spam = False
    show_reports = False
    is_special = False
    can_ban = False
    deleted = False
    rowstyle = 'even'
    reported = False
    collapsed = False
    author = None
    margin = 0

    @staticmethod
    def cache_key(item):
        return False
    
    def __init__(self, link, depth, parent=None):
        if parent:
            self.parent_id = parent._id
            self.parent_name = parent._fullname
            self.parent_permalink = parent.make_permalink(link, 
                                                          link.subreddit_slow)
        self.link_name = link._fullname
        self.link_id = link._id
        self.depth = depth
        self.children = []
        self.count = 0

    @property
    def _fullname(self):
        return self.children[0]._fullname if self.children else 't0_blah'

    @property
    def _id36(self):
        return self.children[0]._id36 if self.children else 't0_blah'


class MoreRecursion(MoreComments):
    pass

class MoreChildren(MoreComments):
    pass
    
class Message(Thing, Printable):
    _defaults = dict(reported = 0,)
    _data_int_props = Thing._data_int_props + ('reported', )

    @classmethod
    def _new(cls, author, to, subject, body, ip, spam = False):
        m = Message(subject = subject,
                    body = body,
                    author_id = author._id,
                    ip = ip)
        m._spam = spam
        m.to_id = to._id
        m._commit()

        #author = Author(author, m, 'author')
        #author._commit()

        # only global admins can be message spammed.
        inbox_rel = None
        if not m._spam or to.name in g.admins:
            inbox_rel = Inbox._add(to, m, 'inbox')

        return (m, inbox_rel)

    @classmethod
    def add_props(cls, user, wrapped):
        #TODO global-ish functions that shouldn't be here?
        #reset msgtime after this request
        msgtime = c.have_messages
        
        #load the "to" field if required
        to_ids = set(w.to_id for w in wrapped)
        tos = Account._byID(to_ids, True) if to_ids else {}

        for item in wrapped:
            item.to = tos[item.to_id]
            if msgtime and item._date >= msgtime:
                item.new = True
            else:
                item.new = False
            item.score_fmt = Score.none

 
    @staticmethod
    def cache_key(wrapped):
        #warning: inbox/sent messages
        #comments as messages
        return False

    def keep_item(self, wrapped):
        return True

class SaveHide(Relation(Account, Link)): pass
class Click(Relation(Account, Link)): pass

class Inbox(MultiRelation('inbox',
                          Relation(Account, Comment),
                          Relation(Account, Message))):
    @classmethod
    def _add(cls, to, obj, *a, **kw):
        i = Inbox(to, obj, *a, **kw)
        i._commit()

        if not to._loaded:
            to._load()
            
        #if there is not msgtime, or it's false, set it
        if not hasattr(to, 'msgtime') or not to.msgtime:
            to.msgtime = obj._date
            to._commit()
            
        return i
