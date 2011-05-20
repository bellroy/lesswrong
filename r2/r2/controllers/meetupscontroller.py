from reddit_base import RedditController
from r2.lib.pages import BoringPage, ShowMeetup, NewMeetup
from validator import validate, VUser, VRequired, VMeetup, VFloat, nop
from errors import errors
from r2.lib.jsonresponse import Json
from routes.util import url_for
from r2.models import Meetup
import json

class MeetupsController(RedditController):
  def response_func(self, **kw):
    return self.sendstring(json.dumps(kw))

  @validate(VUser(),
            title = VRequired('title', None),
            description = VRequired('description', None),
            location = VRequired('location', None),
            date = VRequired('date', None))
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
            latitude = VFloat('latitude', error=errors.NO_LOCATION),
            longitude = VFloat('longitude', error=errors.NO_LOCATION),
            timestamp = VFloat('timestamp', error=errors.INVALID_DATE),
            tzoffset = VFloat('tzoffset', error=errors.INVALID_DATE))
  def POST_create(self, res, title, description, location, latitude, longitude, timestamp, tzoffset):
    if res._chk_error(errors.NO_TITLE):
      res._chk_error(errors.TITLE_TOO_LONG)
      res._focus('title')

    res._chk_errors((errors.NO_LOCATION,
                     errors.NO_DESCRIPTION,
                     errors.INVALID_DATE,
                     errors.NO_DATE))

    if res.error: return

    meetup = Meetup()
    meetup.title = title
    meetup.description = description

    # TODO: Geocode
    meetup.location = location
    meetup.latitude = latitude
    meetup.longitude = longitude

    meetup.timestamp = timestamp / 1000 # Value from form is in ms UTC
    meetup.tzoffset = tzoffset

    meetup._commit()

    res._redirect(url_for(action='show', id=meetup._id36))

  @validate(meetup = VMeetup('id'))
  def GET_show(self, meetup):
    return BoringPage(pagename = meetup.title, content = ShowMeetup(meetup = meetup)).render()

  def GET_edit(self):
    pass
