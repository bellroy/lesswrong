from reddit_base import RedditController
from r2.lib.pages import BoringPage, ShowMeetup, NewMeetup
from validator import validate, VUser, VRequired, VMeetup
from errors import errors
from r2.lib.jsonresponse import Json
import json
from datetime import datetime
from routes.util import url_for
from r2.models import Meetup

class MeetupsController(RedditController):
  def response_func(self, **kw):
    return self.sendstring(json.dumps(kw))

  @validate(VUser(),
            title = VRequired('title', None),
            description = VRequired('description', None),
            location = VRequired('location', None),
            date = VRequired('date', None)) # TODO: Default to today?
  def GET_new(self, title, description, location, date):
    return BoringPage(pagename = 'New Meetup', content = NewMeetup(title=title or '',
                                                                   description=description or '',
                                                                   location=location or '',
                                                                   date=date or '')).render()

  @Json
  @validate(VUser(),
            title = VRequired('title', errors.NO_TITLE),
            description = VRequired('description', errors.NO_DESCRIPTION),
            location = VRequired('location', errors.NO_LOCATION),
            date = VRequired('date', errors.NO_DATE)) # TODO: Make a Date parser/validator
  def POST_create(self, res, title, description, location, date):
    if res._chk_error(errors.NO_TITLE):
      res._chk_error(errors.TITLE_TOO_LONG)
      res._focus('title')

    res._chk_errors((errors.NO_LOCATION, errors.NO_DESCRIPTION, errors.NO_DATE))

    if res.error: return

    meetup = Meetup()
    meetup.title = title
    meetup.location = location
    # TODO: Geocode
    # http://maps.google.com.au/maps?f=q&source=s_q&hl=en&geocode=&q=Level+2,+55+Walsh+ST,+West+Melbourne+VIC+3003,+Australia&sll=-37.41621,144.580027&sspn=0.01406,0.013797&ie=UTF8&hq=&hnear=2%2F55+Walsh+St,+West+Melbourne+Victoria+3003&ll=,&spn=0.006993,0.006899&z=17
    meetup.latitude = -37.808987
    meetup.longitude = 144.951864
    meetup.description = description
    #meetup._date = datetime.strptime(date, "%Y-%m-%d %H:%M")
    meetup._commit()

    res._redirect(url_for('meetup', id=meetup._id))

  def GET_index(self):
    pass

  @validate(meetup = VMeetup('id'))
  def GET_show(self, meetup):
    return BoringPage(pagename = meetup.title, content = ShowMeetup(meetup = meetup)).render()

  def GET_edit(self):
    pass
