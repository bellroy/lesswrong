from r2.controllers.listingcontroller import CommentsController, MeetupslistingController
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
	    return [NamedButton("dashboard", dest="dashboard"),
                NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
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

    @staticmethod
    def staticquery():
        q = Comment._query(Comment.c._spam == (True,False),
                           sort = desc('_interestingness'),
                           eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Comment.c._spam == False)

        q._filter(Thing.c._date >= last_dashboard_visit())

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

class InterestingsubscribedController(CommentsController):
    title_text = _('Leading Subscribed Comments')
    builder_cls = UnbannedCommentBuilder

    @property
    def header_sub_nav(self):
	    return [NamedButton("dashboard", dest="dashboard"),
                NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
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
        if not c.user_is_admin:
            q._filter(Comment.c._spam == False)

        q.prewrap_fn = lambda x: x._thing2

        if self.time == 'last':
            q._filter(SubscriptionStorage.c._date >= last_dashboard_visit())
        elif self.time != 'all':
            q._filter(SubscriptionStorage.c._date >= timeago(queries.relation_db_times[self.time]))

        return q

    @staticmethod
    def staticquery():
        q = SubscriptionStorage._query(SubscriptionStorage.c._thing1_id == c.user._id,
                                       SubscriptionStorage.c._t2_deleted == False,
                                       SubscriptionStorage.c._name == 'subscriptionstorage',
                                       sort = desc('_t2_interestingness'),
                                       eager_load = True,
                                       thing_data = not g.use_query_cache
                                       )
        if not c.user_is_admin:
            q._filter(SubscriptionStorage.c._t2_spam == False)

        q.prewrap_fn = lambda x: x._thing2

        q._filter(SubscriptionStorage.c._date >= last_dashboard_visit())

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
	    return [NamedButton("dashboard", dest="dashboard"),
                NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
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

    @staticmethod
    def staticquery():
        q = Link._query(Link.c._spam == (True,False),
                        sort = desc('_interestingness'),
                        eager_load = True, data = True)
        if not c.user_is_admin:
            q._filter(Link.c._spam == False)

        q._filter(Thing.c._date >= last_dashboard_visit())

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
    @property
    def header_sub_nav(self):
	    return [NamedButton("dashboard", dest="dashboard"),
                NamedButton("leadingsubscribed", dest="dashboard/subscribed"),
                NamedButton("leadingposts", dest="dashboard/posts"),
                NamedButton("leadingcomments", dest="dashboard/comments")]

    render_cls = FormPage
    builder_cls = UnbannedCommentBuilder

    def iterable_builder(self, query):
        b = self.builder_cls(query,
                             num = 3,
                             wrap = self.builder_wrapper,
                             sr_ids = [c.current_or_default_sr._id, Subreddit._by_name('discussion')._id])
        return b

   
    def create_listing(self, controller, title):
        return DashboardListing(self.iterable_builder(controller), title).listing()

    @staticmethod
    def builder_wrapper(thing):
        w = Wrapped(thing)

        if isinstance(thing, Link):
            w.render_class = LinkCompressed

        return w

    def content(self):
        controllers = (InterestingsubscribedController.staticquery(),
                       InterestingpostsController.staticquery(),
                       InterestingcommentsController.staticquery(),
                       CommentsController.staticquery())
        titles = ('Subscribed Comments', 'Leading Posts',
                  'Leading Comments', 'Recent Comments')

        builders = [self.create_listing(*controller) for controller in zip(controllers, titles)]

        self.builder_cls = IDBuilder

        builders.append(self.create_listing(MeetupslistingController.staticquery(), 'Upcoming Meetups'))

        self.builder_cls = UnbannedCommentBuilder
        
        """lb = self.builder(InterestingpostsController.query())
        cb = self.builder(InterestingcommentsController.query())
        sb = self.builder(InterestingsubscribedController.query())
        rcb = self.builder(self.recentcommentsquery())
        mb = self.builder(MeetupslistingController.query())

        ll = DashboardListing(lb)
        cl = DashboardListing(cb)

        lp = PaneStack()
        cp = PaneStack()

        lp.append(ll.listing())
        cp.append(cl.listing())"""

        return Dashtable(*builders)

    @validate(VUser(),
              time = VMenu('where', DashboardTimeMenu))
    def GET_listing(self, time, **env):
        self.time = time
        content = self.content()
        res = FormPage("Dashboard", content = content, header_sub_nav = self.header_sub_nav).render()
        return res
