import os
import sys
from datetime import datetime

from r2.lib.db import tdb_sql as tdb
from r2.lib.db.thing import NotFound, Relation
from r2.models import Link, Comment, Account, Vote, Subreddit
from r2.lib.cache import Memcache, SelfEmptyingCache, CacheChain

from sqlalchemy import *
import pylons

class Exporter:

    def __init__(self, output_db):
        """Initialise with path to output SQLite DB file"""
        # If the output file exists, delete it so that the db is
        # created from scratch
        if os.path.exists(output_db):
            os.unlink(output_db)
        self.db = create_engine("sqlite:///%s" % output_db)

        # Python's encoding handling is reallly annoying
        # http://stackoverflow.com/questions/3033741/sqlalchemy-automatically-converts-str-to-unicode-on-commit
        self.db.raw_connection().connection.text_factory = str
        self.init_db()
        pylons.g.cache = CacheChain((SelfEmptyingCache(max_size=1000), Memcache(pylons.g.memcaches)))

    def export_db(self):
        self.started_at = datetime.now()
        self.export_users()
        self.export_links()
        self.export_comments()
        self.export_votes()
        self.create_indexes()
        print >>sys.stderr, "Finished, total run time %d secs" % ((datetime.now() - self.started_at).seconds,)

    def export_thing(self, thing_class, table, row_extract):
        processed = 0
        max_id = self.max_thing_id(thing_class)
        print >>sys.stderr, "%d %s to process" % (max_id, table.name)
        for thing_id in xrange(max_id):
            try:
                thing = thing_class._byID(thing_id, data=True)
            except NotFound:
                continue

            try:
                row = row_extract(thing)
            except AttributeError:
                print >>sys.stderr, "  thing with id %d is broken, skipping" % thing_id
                continue

            table.insert(values=row).execute()
            processed += 1
            self.update_progress(processed)

    def user_row_extract(self, account):
        return (
            account._id,
            self.utf8(account.name),
            account.email if hasattr(account, 'email') else None,
            account.link_karma,
            account.comment_karma
        )

    def export_users(self):
        self.export_thing(Account, self.users, self.user_row_extract)

    def article_row_extract(self, link):
        sr = Subreddit._byID(link.sr_id, data=True)
        row = (
            link._id,
            self.utf8(link.title),
            self.utf8(link.article),
            link.author_id,
            link._date,
            sr.name
        )
        return row

    def export_links(self):
        self.export_thing(Link, self.articles, self.article_row_extract)

    def comment_row_extract(self, comment):
        return (
            comment._id,
            comment.author_id,
            comment.link_id,
            comment.body,
            comment._date
        )

    def export_comments(self):
        self.export_thing(Comment, self.comments, self.comment_row_extract)

    def export_votes(self):
        self.export_rel_votes(Link, self.article_votes)
        self.export_rel_votes(Comment, self.comment_votes)

    def export_rel_votes(self, votes_on_cls, table):
        # Vote.vote(c.user, link, action == 'like', request.ip)
        processed = 0
        rel = Vote.rel(Account, votes_on_cls)
        max_id = self.max_rel_type_id(rel)
        print >>sys.stderr, "%d %s to process" % (max_id, table.name)
        for vote_id in xrange(max_id):
            try:
                vote = rel._byID(vote_id, data=True)
            except NotFound:
                continue

            try:
                row = (
                    vote._id,
                    vote._thing1_id, # Account
                    vote._thing2_id, # Link/Comment (votes_on_cls)
                    vote._name, # Vote value
                    vote._date
                )
            except AttributeError:
                print >>sys.stderr, "  vote with id %d is broken, skipping" % vote_id
                continue

            table.insert(values=row).execute()
            processed += 1
            self.update_progress(processed)

    def max_rel_type_id(self, rel_thing):
        thing_type = tdb.rel_types_id[rel_thing._type_id]
        thing_tbl = thing_type.rel_table[0]
        rows = select([func.max(thing_tbl.c.rel_id)]).execute().fetchall()
        return rows[0][0]

    def max_thing_id(self, thing):
        thing_type = tdb.types_id[thing._type_id]
        thing_tbl = thing_type.thing_table
        rows = select([func.max(thing_tbl.c.thing_id)]).execute().fetchall()
        return rows[0][0]

    def utf8(self, text):
        if isinstance(text, unicode):
            try:
                text = text.encode('utf-8')
            except UnicodeEncodeError:
                print >>sys.stderr, "UnicodeEncodeError, using 'ignore' error mode" % link._id
                text = text.encode('utf-8', errors='ignore')
        elif isinstance(text, str):
            try:
                text = text.decode('utf-8').encode('utf-8')
            except UnicodeError:
                print >>sys.stderr, "UnicodeError, using 'ignore' error mode" % link._id
                text = text.decode('utf-8', errors='ignore').encode('utf-8', errors='ignore')

        return text

    def init_db(self):
        self.users = Table('users', self.db,
            Column('id', Integer, primary_key=True),
            Column('name', VARCHAR()),
            Column('email', VARCHAR()),
            Column('article_karma', Integer),
            Column('comment_karma', Integer),
        )
        self.users.create()

        self.articles = Table('articles', self.db,
            Column('id', Integer, primary_key=True),
            Column('title', VARCHAR()),
            Column('body', TEXT()),
            Column('author_id', Integer, ForeignKey('users.id')),
            Column('updated_at', DateTime()),
            Column('subreddit', VARCHAR()),
        )
        self.articles.create()

        self.comments = Table('comments', self.db,
            Column('id', Integer, primary_key=True),
            Column('author_id', Integer, ForeignKey('users.id')),
            Column('article_id', Integer, ForeignKey('articles.id')),
            Column('body', TEXT()),
            Column('updated_at', DateTime()),
        )
        self.comments.create()

        self.article_votes = Table('article_votes', self.db,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.id')),
            Column('article_id', Integer, ForeignKey('articles.id')),
            Column('vote', Integer()),
            Column('updated_at', DateTime()),
        )
        self.article_votes.create()

        self.comment_votes = Table('comment_votes', self.db,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.id')),
            Column('comment_id', Integer, ForeignKey('comments.id')),
            Column('vote', Integer()),
            Column('updated_at', DateTime()),
        )
        self.comment_votes.create()

    def create_indexes(self):
        #i = Index('someindex', sometable.c.col5)
        print >>sys.stderr, "Creating indexes on users table"
        Index('ix_users_id', self.users.c.id).create()
        Index('ix_users_name', self.users.c.name).create()
        Index('ix_users_email', self.users.c.email).create()
        print >>sys.stderr, "Creating indexes on articles table"
        Index('ix_articles_id', self.articles.c.id).create()
        Index('ix_articles_author_id', self.articles.c.author_id).create()
        Index('ix_articles_title', self.articles.c.title).create()
        print >>sys.stderr, "Creating indexes on comments table"
        Index('ix_comments_id', self.comments.c.id).create()
        Index('ix_comments_author_id', self.comments.c.author_id).create()
        Index('ix_comments_article_id', self.comments.c.article_id).create()
        print >>sys.stderr, "Creating indexes on article_votes table"
        Index('ix_article_votes_id', self.article_votes.c.id).create()
        Index('ix_article_votes_author_id', self.article_votes.c.user_id).create()
        Index('ix_article_votes_article_id', self.article_votes.c.article_id).create()
        Index('ix_article_votes_vote', self.article_votes.c.vote).create()
        print >>sys.stderr, "Creating indexes on comment_votes table"
        Index('ix_comment_votes_id', self.comment_votes.c.id).create()
        Index('ix_comment_votes_author_id', self.comment_votes.c.user_id).create()
        Index('ix_comment_votes_comment_id', self.comment_votes.c.comment_id).create()
        Index('ix_comment_votes_vote', self.comment_votes.c.vote).create()

    def update_progress(self, done):
        """print a progress message"""
        if done % 100 == 0:
            print >>sys.stderr, "  %d processed, run time %d secs" % (done, (datetime.now() - self.started_at).seconds)
