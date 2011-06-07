from reddit_base import RedditController
from r2.lib.pages import BoringPage, ShowMeetup, NewMeetup, EditMeetup, PaneStack, CommentListing, LinkInfoPage, CommentReplyBox
from validator import validate, VUser, VRequired, VMeetup, VEditMeetup, VFloat, ValueOrBlank, ValidIP
from errors import errors
from r2.lib.jsonresponse import Json
from routes.util import url_for
from r2.models import Meetup,Link,Subreddit,CommentBuilder
from r2.models.listing import NestedListing
from r2.lib.menus import CommentSortMenu,NumCommentsMenu
from r2.lib.filters import python_websafe
from pylons import c,g,request
import json

class MeetupsController(RedditController):
  def response_func(self, **kw):
    return self.sendstring(json.dumps(kw))

  @validate(VUser(),
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
            ip = ValidIP(),
            title = VRequired('title', errors.NO_TITLE),
            description = VRequired('description', errors.NO_DESCRIPTION),
            location = VRequired('location', errors.NO_LOCATION),
            latitude = VFloat('latitude', error=errors.NO_LOCATION),
            longitude = VFloat('longitude', error=errors.NO_LOCATION),
            timestamp = VFloat('timestamp', error=errors.INVALID_DATE),
            tzoffset = VFloat('tzoffset', error=errors.INVALID_DATE))
  def POST_create(self, res, title, description, location, latitude, longitude, timestamp, tzoffset, ip):
    if res._chk_error(errors.NO_TITLE):
      res._chk_error(errors.TITLE_TOO_LONG)
      res._focus('title')

    res._chk_errors((errors.NO_LOCATION,
                     errors.NO_DESCRIPTION,
                     errors.INVALID_DATE,
                     errors.NO_DATE))

    if res.error: return

    meetup = Meetup(
      author_id = c.user._id,

      title = title,
      description = description,

      location = location,
      latitude = latitude,
      longitude = longitude,

      timestamp = timestamp / 1000, # Value from form is in ms UTC
      tzoffset = tzoffset
    )

    # Expire all meetups in the render cache
    g.rendercache.invalidate_key_group(Meetup.group_cache_key())

    meetup._commit()
    l = Link._submit(title, 
                     "Discussion for the meetup <a href='%s'>%s</a>"
                     %(url_for(controller='meetups',action='show',id=meetup._id36),
                       python_websafe(title)),
                     c.user, Subreddit._by_name('discussion'),ip, [])

    l.meetup = meetup._id36
    l._commit()
    meetup.assoc_link = l._id
    meetup._commit()

    #update the queries
    if g.write_query_queue:
      queries.new_link(l)

    res._redirect(url_for(action='show', id=meetup._id36))

  @Json
  @validate(VUser(),
            meetup = VEditMeetup('id'),
            title = VRequired('title', errors.NO_TITLE),
            description = VRequired('description', errors.NO_DESCRIPTION),
            location = VRequired('location', errors.NO_LOCATION),
            latitude = VFloat('latitude', error=errors.NO_LOCATION),
            longitude = VFloat('longitude', error=errors.NO_LOCATION),
            timestamp = VFloat('timestamp', error=errors.INVALID_DATE),
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

    meetup.timestamp = timestamp / 1000 # Value from form is in ms UTC
    meetup.tzoffset = tzoffset

    # Expire all meetups in the render cache
    g.rendercache.invalidate_key_group(Meetup.group_cache_key())

    meetup._commit()

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
  # TODO, re-introduce the comment filters and sorting.
  @validate(meetup = VMeetup('id'))
  def GET_show(self, meetup):
    article = Link._byID(meetup.assoc_link)
    sort = 'old'
    num_comments = g.max_comments
    builder = CommentBuilder(article, CommentSortMenu.operator(sort), None, None)
    listing = NestedListing(builder, num=num_comments, parent_name = article._fullname)
    displayPane = PaneStack()
    
    # insert reply box only for logged in user
    if c.user_is_loggedin:
      displayPane.append(CommentReplyBox())
      displayPane.append(CommentReplyBox(link_name = 
                                         article._fullname))

    # finally add the comment listing
    displayPane.append(listing.listing())

    # sort_menu = CommentSortMenu(default = sort)
    # if hasattr(article, 'comment_sort_order'):
    #   sort_menu.enabled = False
    # nav_menus = [sort_menu,
    #              NumCommentsMenu(article.num_comments,
    #                              default=num_comments)]

    content = CommentListing(
      content = displayPane,
      num_comments = article.num_comments,
      #nav_menus = nav_menus,
      )


    # is_canonical indicates if the page is the canonical location for
    # the resource. The canonical location is deemed to be one with
    # no query string arguments
    # res = LinkInfoPage(link = article, comment = None,
    #                    content = content, 
    #                    infotext = None,
    #                    is_canonical = True).render()
    
    lastViewed = None
    if c.user_is_loggedin:
      clicked = article._getLastClickTime(c.user)
      lastViewed = clicked._date if clicked else None
      article._click(c.user)

    res = ShowMeetup(meetup = meetup, content = content, 
                     fullname=article._fullname,
                     lastViewed = lastViewed)

    return BoringPage(pagename = meetup.title, 
                      content = res).render()


