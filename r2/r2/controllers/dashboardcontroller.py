from r2.controllers.listingcontroller import CommentsController
from r2.models import *
from validator import *
from r2.lib.pages import *
from r2.lib.menus import DashboardTimeMenu
from r2.lib.db import queries

from pylons.i18n import _

from datetime import datetime

def last_dashboard_visit():
    hc_key = "dashboard_visit-%s" % c.user.name
    cache_visit = g.permacache.get(hc_key, None)
    if cache_visit:
        return cache_visit
    else:
        last_visit = c.user.dashboard_visit
        g.permacache.set(hc_key, last_visit, time = int(g.dashboard_visits_period)) 
        c.user.dashboard_visit = datetime.now(g.tz)
        c.user._commit()
        return last_visit

class InterestingcommentsController(CommentsController):
    title_text = _('Leading Comments')
    builder_cls = UnbannedCommentBuilder

    @property
    def header_sub_nav(self):
	    return [NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
                NamedButton("leadingposts", dest="dashboard/posts"),
                NamedButton("leadingcomments", dest="dashboard/comments")]

    def query(self):
        q = Comment._query(Comment.c._spam == (True,False),
                           sort = desc('_interestingness'),
                           eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Comment.c._spam == False)

        if self.time == 'last':
            q._filter(Thing.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(queries.db_times[self.time])

        return q

    def builder(self):
        b = self.builder_cls(self.query_obj,
                             num = self.num,
                             skip = self.skip,
                             after = self.after,
                             count = self.count,
                             reverse = self.reverse,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id, Subreddit._by_name('discussion')._id])
        return b

    @property
    def top_filter(self):
        return DashboardTimeMenu(default = self.time, title = _('Filter'), type='dropdown2')

    @validate(VUser(),
              time = VMenu('where', DashboardTimeMenu))
    def GET_listing(self, time, **env):
        self.time = time
        return CommentsController.GET_listing(self, **env)

class ListingtestController(CommentsController):
    def commentquery(self):
        q = Comment._query(Comment.c._spam == (True,False),
                           sort = desc('_interestingness'),
                           eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Comment.c._spam == False)

        if self.time == 'last':
            q._filter(Thing.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(queries.db_times[self.time])

        return q

    def linkquery(self):
        q = Link._query(Link.c._spam == (True,False),
                        sort = desc('_interestingness'),
                        eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Link.c._spam == False)

        if self.time == 'last':
            q._filter(Thing.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(queries.db_times[self.time])

        return q

    def builder(self, query):
        b = self.builder_cls(query,
                             num = 3,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id, Subreddit._by_name('discussion')._id])
        return b

    def content(self):
        lb = self.builder(self.linkquery())
        cb = self.builder(self.commentquery())

        ll = DashboardListing(lb)
        cl = DashboardListing(cb)
        
        displayPane = PaneStack()

        displayPane.append(ll.listing())
        displayPane.append(cl.listing())

        return displayPane

    @validate(VUser(),
              time = VMenu('where', DashboardTimeMenu))
    def GET_listing(self, time, **env):
        self.time = time
        return CommentsController.GET_listing(self, **env)

class InterestingsubscribedController(CommentsController):
    title_text = _('Leading Subscribed Comments')
    builder_cls = UnbannedCommentBuilder

    @property
    def header_sub_nav(self):
	    return [NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
                NamedButton("leadingposts", dest="dashboard/posts"),
                NamedButton("leadingcomments", dest="dashboard/comments")]

    def query(self):
        q = SubscriptionStorage._query(SubscriptionStorage.c._thing1_id == c.user._id,
                                       SubscriptionStorage.c._t2_deleted == False,
                                       SubscriptionStorage.c._name == 'subscriptionstorage',
                                       sort = desc('_t2_interestingness'),
                                       eager_load = True,
                                       thing_data = not g.use_query_cache
                                       )
        #if not c.user_is_admin:
        #    q._filter(Comment.c._spam == False)

        q.prewrap_fn = lambda x: x._thing2

        if self.time == 'last':
            q._filter(SubscriptionStorage.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(SubscriptionStorage.c._date >= timeago(queries.relation_db_times[self.time]))

        return q

    def builder(self):
        b = self.builder_cls(self.query_obj,
                             num = self.num,
                             skip = self.skip,
                             after = self.after,
                             count = self.count,
                             reverse = self.reverse,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id, Subreddit._by_name('discussion')._id])
        return b

    @property
    def top_filter(self):
        return DashboardTimeMenu(default = self.time, title = _('Filter'), type='dropdown2')

    @validate(VUser(),
              time = VMenu('where', DashboardTimeMenu))
    def GET_listing(self, time, **env):
        self.time = time
        return CommentsController.GET_listing(self, **env)

class InterestingpostsController(CommentsController):
    title_text = _('Leading Posts')
    builder_cls = QueryBuilder

    @property
    def header_sub_nav(self):
	    return [NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
                NamedButton("leadingposts", dest="dashboard/posts"),
                NamedButton("leadingcomments", dest="dashboard/comments")]

    def query(self):
        q = Link._query(Link.c._spam == (True,False),
                        sort = desc('_interestingness'),
                        eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Link.c._spam == False)

        if self.time == 'last':
            q._filter(Thing.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(queries.db_times[self.time])

        return q

    def builder(self):
        b = self.builder_cls(self.query_obj,
                             num = self.num,
                             skip = self.skip,
                             after = self.after,
                             count = self.count,
                             reverse = self.reverse,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id, Subreddit._by_name('discussion')._id])
        return b

    @property
    def top_filter(self):
        return DashboardTimeMenu(default = self.time, title = _('Filter'), type='dropdown2')

    @validate(VUser(),
              time = VMenu('where', DashboardTimeMenu))
    def GET_listing(self, time, **env):
        self.time = time
        return CommentsController.GET_listing(self, **env)
