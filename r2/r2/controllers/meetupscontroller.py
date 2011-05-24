from reddit_base import RedditController
from r2.lib.pages import BoringPage, ShowMeetup, NewMeetup, EditMeetup
from validator import validate, VUser, VRequired, VMeetup, VEditMeetup, VFloat, nop
from errors import errors
from r2.lib.jsonresponse import Json
from routes.util import url_for
from r2.models import Meetup
from pylons import c
import json

class MeetupsController(RedditController):
  def response_func(self, **kw):
    return self.sendstring(json.dumps(kw))

  @validate(VUser(),
            title = nop('title'),
            description = nop('description'),
            location = nop('location'),
            timestamp = nop('timestamp'))
  def GET_new(self, title, description, location, date):
    return BoringPage(pagename = 'New Meetup', content = NewMeetup(title=title or '',
                                                                   description=description or '',
                                                                   location=location or '',
                                                                   timestamp=timestamp or '')).render()

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

    meetup = Meetup(
      author_id = c.user._id,

      title = title,
      description = description,

      # TODO: Geocode
      location = location,
      latitude = latitude,
      longitude = longitude,

      timestamp = timestamp / 1000, # Value from form is in ms UTC
      tzoffset = tzoffset
    )

    meetup._commit()

    res._redirect(url_for(action='show', id=meetup._id36))

  @validate(meetup = VMeetup('id'))
  def GET_show(self, meetup):
    return BoringPage(pagename = meetup.title, content = ShowMeetup(meetup = meetup)).render()

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
