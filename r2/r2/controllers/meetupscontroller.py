from datetime import datetime, timedelta
import json
import calendar

from mako.template import Template
from pylons.i18n import _
from pylons import c,g,request

from reddit_base import RedditController
from r2.lib.errors import errors
from r2.lib.filters import python_websafe
from r2.lib.jsonresponse import Json
from r2.lib.menus import CommentSortMenu,NumCommentsMenu
from r2.lib.pages import BoringPage, ShowMeetup, NewMeetup, EditMeetup, PaneStack, CommentListing, LinkInfoPage, CommentReplyBox, NotEnoughKarmaToPost, CancelMeetup, UnfoundPage
from r2.models import Meetup,Link,Subreddit,CommentBuilder,PendingJob,Account
from r2.models.listing import NestedListing
from validator import validate, VUser, VModhash, VRequired, VMeetup, VEditMeetup, VFloat, ValueOrBlank, ValidIP, VMenu, VCreateMeetup, VTimestamp, nop
from routes.util import url_for


def meetup_article_text(meetup):
  t = Template(filename="r2/templates/showmeetup.html", output_encoding='utf-8', encoding_errors='replace')
  res = t.get_def("meetup_info").render_unicode(meetup=meetup)

  url = url_for(controller='meetups',action='show',id=meetup._id36)
  title = python_websafe(meetup.title)
  hdr = u"<h2>Discussion article for the meetup : <a href='%s'>%s</a></h2>"%(url,title)
  return hdr+res+hdr

def meetup_article_title(meetup):
  return "Meetup : %s"%meetup.title

def calculate_month_interval(date):
  """Calculates the number of days between a date
  and the same day (ie 3rd Wednesday) in the
  following month"""

  day_of_week = date.weekday()
  week_of_month = (date.day-1)/7
  this_month = (date.year, date.month)
  if this_month[1] != 12:
    next_month = (this_month[0], this_month[1]+1)
  else:
    next_month = (this_month[0] + 1, 1)
  this_month = calendar.monthrange(*this_month)
  next_month = calendar.monthrange(*next_month)
  remaining_days_in_month = this_month[1] - date.day
  """this line calculates the nth day of the next month,
  if that exceeds the number of days in that month, it 
  backs off a week"""
  days_into_next_month = (day_of_week - next_month[0])%7 + (week_of_month * 7 + 1) if (day_of_week - next_month[0])%7 + week_of_month * 7 + 1 < next_month[1] else (day_of_week - next_month[0])%7 + (week_of_month-1) * 7 + 1 
  offset = remaining_days_in_month + days_into_next_month
  return offset

class MeetupsController(RedditController):
  def response_func(self, **kw):
    return self.sendstring(json.dumps(kw))

  @validate(VUser(), 
            VCreateMeetup(),
            title = ValueOrBlank('title'),
            description = ValueOrBlank('description'),
            location = ValueOrBlank('location'),
            latitude = ValueOrBlank('latitude'),
            longitude = ValueOrBlank('longitude'),
            timestamp = ValueOrBlank('timestamp'),
            tzoffset = ValueOrBlank('tzoffset'))
  def GET_new(self, *a, **kw):
    return BoringPage(pagename = 'New Meetup', content = NewMeetup(*a, **kw)).render()

  @Json
  @validate(VUser(),
            VCreateMeetup(),
            VModhash(),
            ip = ValidIP(),
            title = VRequired('title', errors.NO_TITLE),
            description = VRequired('description', errors.NO_DESCRIPTION),
            location = VRequired('location', errors.NO_LOCATION),
            latitude = VFloat('latitude', error=errors.NO_LOCATION),
            longitude = VFloat('longitude', error=errors.NO_LOCATION),
            timestamp = VTimestamp('timestamp'),
            tzoffset = VFloat('tzoffset', error=errors.INVALID_DATE),
            recurring = nop('recurring'))
  def POST_create(self, res, title, description, location, latitude, longitude, timestamp, tzoffset, ip, recurring):
    if res._chk_error(errors.NO_TITLE):
      res._chk_error(errors.TITLE_TOO_LONG)
      res._focus('title')

    if recurring != 'never':
        try:
            Account._byID(c.user._id).email
        except:
            res._set_error(errors.CANT_RECUR)

    res._chk_errors((errors.NO_LOCATION,
                     errors.NO_DESCRIPTION,
                     errors.INVALID_DATE,
                     errors.NO_DATE,
                     errors.CANT_RECUR))

    if res.error: return

    meetup = self.create(c.user._id, title, description, location, latitude, longitude, timestamp, tzoffset, ip, recurring)

    res._redirect(url_for(action='show', id=meetup._id36))

  @validate(key = nop('key'))
  def GET_stopmeetup(self, key):
    try:
        pj = list(PendingJob._query(PendingJob.c._id == key, data=True))[0]
        pj._delete_from_db()
        return BoringPage(_("Cancel Meetup"),
                          content=CancelMeetup()).render()
    except:
        return BoringPage(_("Page not found"),
                          content=UnfoundPage()).render()

  def create(self, author_id, title, description, location, latitude, longitude, timestamp, tzoffset, ip, recurring):
    meetup = Meetup(
      author_id = author_id,

      title = title,
      description = description,

      location = location,
      latitude = latitude,
      longitude = longitude,

      timestamp = timestamp,
      tzoffset = tzoffset
    )

    # Expire all meetups in the render cache
    g.rendercache.invalidate_key_group(Meetup.group_cache_key())

    meetup._commit()

    l = Link._submit(meetup_article_title(meetup), meetup_article_text(meetup),
                     Account._byID(author_id, data=True), Subreddit._by_name('discussion'),ip, [])

    l.meetup = meetup._id36
    l._commit()
    meetup.assoc_link = l._id
    meetup._commit()

    when = datetime.now(g.tz) + timedelta(0, 60) # Leave a short window of time before notification, in case
                                                    # the meetup is edited/deleted soon after its creation
    PendingJob.store(when, 'process_new_meetup', {'meetup_id': meetup._id})

    if recurring != 'never':
        if recurring == 'weekly':
            offset = 7
        elif recurring == 'biweekly':
            offset = 14
        elif recurring == 'monthly':
            offset =  calculate_month_interval(meetup.datetime())

        data = {'author_id':author_id,'title':title,'description':description,'location':location,
                'latitude':latitude,'longitude':longitude,'timestamp':timestamp+offset*86400,
                'tzoffset':tzoffset,'ip':ip,'recurring':recurring}

        when = datetime.now(g.tz) + timedelta(offset-15)

        PendingJob.store(when, 'meetup_repost_emailer', data)


    #update the queries
    if g.write_query_queue:
      queries.new_link(l)

    return meetup

  @Json
  @validate(VUser(),
            VModhash(),
            meetup = VEditMeetup('id'),
            title = VRequired('title', errors.NO_TITLE),
            description = VRequired('description', errors.NO_DESCRIPTION),
            location = VRequired('location', errors.NO_LOCATION),
            latitude = VFloat('latitude', error=errors.NO_LOCATION),
            longitude = VFloat('longitude', error=errors.NO_LOCATION),
            timestamp = VTimestamp('timestamp'),
            tzoffset = VFloat('tzoffset', error=errors.INVALID_DATE))
  def POST_update(self, res, meetup, title, description, location, latitude, longitude, timestamp, tzoffset):
    if res._chk_error(errors.NO_TITLE):
      res._chk_error(errors.TITLE_TOO_LONG)
      res._focus('title')

    res._chk_errors((errors.NO_LOCATION,
                     errors.NO_DESCRIPTION,
                     errors.INVALID_DATE,
                     errors.NO_DATE))

    if res.error: return

    meetup.title = title
    meetup.description = description

    meetup.location = location
    meetup.latitude = latitude
    meetup.longitude = longitude

    meetup.timestamp = timestamp
    meetup.tzoffset = tzoffset

    # Expire all meetups in the render cache
    g.rendercache.invalidate_key_group(Meetup.group_cache_key())

    meetup._commit()

    # Update the linked article
    article = Link._byID(meetup.assoc_link)
    article._load()
    article_old_url = article.url
    article.title = meetup_article_title(meetup)
    article.article = meetup_article_text(meetup)
    article._commit()
    article.update_url_cache(article_old_url)


    res._redirect(url_for(action='show', id=meetup._id36))

  @validate(VUser(),
            meetup = VEditMeetup('id'))
  def GET_edit(self, meetup):
    return BoringPage(pagename = 'Edit Meetup', content = EditMeetup(meetup,
                                                                     title=meetup.title,
                                                                     description=meetup.description,
                                                                     location=meetup.location,
                                                                     latitude=meetup.latitude,
                                                                     longitude=meetup.longitude,
                                                                     timestamp=int(meetup.timestamp * 1000),
                                                                     tzoffset=meetup.tzoffset)).render()

  # Show a meetup.  Most of this code was coped from GET_comments in front.py
  @validate(meetup = VMeetup('id'),
            sort         = VMenu('controller', CommentSortMenu),
            num_comments = VMenu('controller', NumCommentsMenu))
  def GET_show(self, meetup, sort, num_comments):
    article = Link._byID(meetup.assoc_link)

    # figure out number to show based on the menu
    user_num = c.user.pref_num_comments or g.num_comments
    num = g.max_comments if num_comments == 'true' else user_num

    builder = CommentBuilder(article, CommentSortMenu.operator(sort), None, None)
    listing = NestedListing(builder, num=num, parent_name = article._fullname)
    displayPane = PaneStack()
    
    # insert reply box only for logged in user
    if c.user_is_loggedin:
      displayPane.append(CommentReplyBox())
      displayPane.append(CommentReplyBox(link_name = 
                                         article._fullname))

    # finally add the comment listing
    displayPane.append(listing.listing())

    sort_menu = CommentSortMenu(default = sort, type='dropdown2')
    nav_menus = [sort_menu,
                 NumCommentsMenu(article.num_comments,
                                 default=num_comments)]

    content = CommentListing(
      content = displayPane,
      num_comments = article.num_comments,
      nav_menus = nav_menus,
      )


    # Update last viewed time, and return the previous last viewed time.  Actually tracked on the article
    lastViewed = None
    if c.user_is_loggedin:
      clicked = article._getLastClickTime(c.user)
      lastViewed = clicked._date if clicked else None
      article._click(c.user)

    res = ShowMeetup(meetup = meetup, content = content, 
                     fullname=article._fullname,
                     lastViewed = lastViewed)

    return BoringPage(pagename = meetup.title, 
                      content = res,
                      body_class = 'meetup').render()


