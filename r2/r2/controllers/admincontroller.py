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
from reddit_base import RedditController, base_listing
from validator import *

from r2.models import *
from r2.lib.pages import *
from r2.lib.wrapped import Wrapped
from r2.lib.db.thing import Query, Merge, Relations
from r2.lib.db import queries

from pylons.i18n import _


class VotemultiplierController(RedditController):
    """Admin page to set a user's vote multiplier.

    Votes by that user are scaled by that multiplier.
    Vote multiplier of 1 is default.
    Vote multiplier of 0 means a users votes don't award any karma.
    Vote multiplier of 2 means a users votes count for twice as much karma.
    """
    # page title
    title_text = ''

    # login box, subreddit box, submit box, etc, visible
    show_sidebar = True

    # class (probably a subclass of Reddit) to use to render the page.
    render_cls = Reddit

    #extra parameters to send to the render_cls constructor
    render_params = {}

    def title(self):
        return "Edit Vote Multiplier for %s" % (self.vuser.name)

    def rightbox(self):
        """Contents of the right box when rendering"""
        pass

    @validate(vuser = VExistingUname('username'),
              multiplier = nop('multiplier'),
              success = nop('success'))
    def GET_edit(self, vuser, multiplier, success):
        if not c.user_is_admin:
            return self.abort404()
        if not vuser or vuser._deleted:
            return self.abort404()

        self.vuser = vuser
        captcha = Captcha() if c.user.needs_captcha() else None
        page = VoteMultiplierEditPage(self.title(), vuser, captcha)
        return page.render()
