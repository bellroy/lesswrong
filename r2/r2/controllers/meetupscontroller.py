from reddit_base import RedditController
from r2.lib.pages import BoringPage, ShowMeetup
from validator import VMeetup, validate

class MeetupsController(RedditController):
  def GET_new(self):
    #return EditReddit(content = pane).render()
    pass

  def GET_index(self):
    pass

  @validate(meetup = VMeetup('id'))
  def GET_show(self, meetup):
    return BoringPage(pagename = meetup.title, content = ShowMeetup(meetup = meetup)).render()

  def GET_edit(self):
    pass
