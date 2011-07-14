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
"""
Setup your Routes options here
"""
import os
from routes import Mapper
import admin_routes
from wiki_pages_embed import allWikiPagesCached

def make_map(global_conf={}, app_conf={}):
    map = Mapper()
    mc = map.connect

    admin_routes.add(mc)

    mc('/login',    controller='front', action='login')
    mc('/logout',   controller='front', action='logout')
    mc('/adminon',  controller='front', action='adminon')
    mc('/adminoff', controller='front', action='adminoff')
    mc('/submit',   controller='front', action='submit')

    mc('/imagebrowser', controller='front', action='imagebrowser')
    mc('/imagebrowser/:article', controller='front', action='imagebrowser')

    mc('/validuser',   controller='front', action='validuser')

    mc('/over18',   controller='post', action='over18')

    mc('/search/results', controller='front', action='search_results')

    mc('/about/:location', controller='front',
       action='editreddit', location = 'about')

    mc('/categories/create', controller='front', action='newreddit')
    mc('/categories/:where', controller='reddits', action='listing',
       where = 'popular',
       requirements=dict(where="popular|new|banned"))

    mc('/categories/mine/:where', controller='myreddits', action='listing',
       where='subscriber',
       requirements=dict(where='subscriber|contributor|moderator'))

    #mc('/stats', controller='front', action='stats')

    mc('/user/:username/:where', controller='user', action='listing',
       where='overview')

    mc('/prefs/:location', controller='front',
       action='prefs', location='options')

    mc('/related/:article/:title', controller='front',
       action = 'related', title=None)
    mc('/lw/:article/:title/:comment', controller='front',
       action= 'comments', title=None, comment = None)
    mc('/edit/:article', controller='front', action="editarticle")


    mc('/stylesheet', controller = 'front', action = 'stylesheet')

    mc('/', controller='promoted', action='listing')
    
    for name,page in allWikiPagesCached.items():
        if page.has_key('route'):
            mc("/wiki/"+page['route'], controller='wikipage', action='wikipage', name=name)
        
    mc('/invalidate_cache/:name', controller='wikipage', action='invalidate_cache')

    listing_controllers = "hot|saved|toplinks|topcomments|new|recommended|randomrising|comments|blessed|recentposts|edits|promoted"

    mc('/:controller', action='listing',
       requirements=dict(controller=listing_controllers))

    # Can't use map.resource because the version of the Routing module we're
    # using doesn't support the controller_action kw arg
    #map.resource('meetup', 'meetups', collection_actions=['create', 'new'])
    mc('/meetups/create', action='create', controller='meetups')
    mc('/meetups', action='listing', controller='meetupslisting')
    mc('/meetups/new', action='new', controller='meetups')
    mc('/meetups/:id/edit', action='edit', controller='meetups')
    mc('/meetups/:id/update', action='update', controller='meetups')
    mc('/meetups/:id', action='show', controller='meetups')

    mc('/tag/:tag', controller='tag', action='listing', where='tag')

    mc('/by_id/:names', controller='byId', action='listing')

    mc('/:sort', controller='browse', sort='top', action = 'listing',
       requirements = dict(sort = 'top|controversial'))

    mc('/message/compose', controller='message', action='compose')
    mc('/message/:where', controller='message', action='listing')

    mc('/:action', controller='front',
       requirements=dict(action="password|random|framebuster"))
    mc('/:action', controller='embed',
       requirements=dict(action="help|blog"))

    mc('/:action', controller='toolbar',
       requirements=dict(action="goto|toolbar"))

    mc('/resetpassword/:key', controller='front',
       action='resetpassword')
    mc('/resetpassword', controller='front',
       action='resetpassword')

    mc('/post/:action', controller='post',
       requirements=dict(action="options|over18|optout|optin|login|reg"))

    mc('/api/:action', controller='api')

    mc('/captcha/:iden', controller='captcha', action='captchaimg')

    mc('/doquery', controller='query', action='doquery')

    mc('/code', controller='redirect', action='redirect',
       dest='http://code.google.com/p/lesswrong/')

    mc('/about-less-wrong', controller='front', action='about')
    mc('/issues', controller='front', action='issues')

    # Google webmaster tools verification page
    mc('/googlea26ba8329f727095.html', controller='front', action='blank')

    # This route handles displaying the error page and
    # graphics used in the 404/500
    # error pages. It should likely stay at the top
    # to ensure that the error page is
    # displayed properly.
    mc('/error/document/:id', controller='error', action="document")

    mc("/*url", controller='front', action='catchall')

    return map

