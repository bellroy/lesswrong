# Initialise a newly-created db with required tables, users,
# categories and tags.
from r2.lib.db.thing import NotFound
from r2.models.account import Account, AccountExists, register
from r2.models.link import Tag, TagExists
from r2.models.subreddit import Subreddit

try:
    register('admin', 'swordfish', '')
except AccountExists:
    pass

admin = Account._by_name('admin')
admin.email_validated = True

try:
    Subreddit._by_name('lesswrong')
except NotFound:
    Subreddit._create_and_subscribe('lesswrong', admin,
                                    { 'title': 'Less Wrong',
                                      'type': 'restricted',
                                      'default_listing': 'blessed' })

try:
    Subreddit._by_name('discussion')
except NotFound:
    Subreddit._create_and_subscribe('discussion', admin,
                                    { 'title': 'Less Wrong Discussion',
                                      'type': 'public',
                                      'default_listing': 'new' })

tags = ['group_rationality_diary', 'open_thread', 'quotes']
for tag in tags:
    try:
        Tag._new(tag)
    except TagExists:
        pass
