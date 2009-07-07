import os
import sys

from r2.lib.db import tdb_sql as tdb
from r2.lib.db.thing import NotFound, Relation
from r2.models import Link, Comment, Account, Vote, Subreddit

from sqlalchemy import *

class Exporter:
    
    def __init__(self, output_db):
        """Initialise with path to output SQLite DB file"""
        # If the output file exists, delete it so that the db is
        # created from scratch
        if os.path.exists(output_db):
            os.unlink(output_db)
        self.db = create_engine("sqlite:///%s" % output_db)
        self.init_db()

    def export_db(self):
        self.export_users()
        self.export_links()
        self.export_comments()
        self.export_votes()

    def export_users(self):
        max_id = self.max_thing_id(Account)
        table = Table('users', self.db, autoload=True)
        print >>sys.stderr, insert
        print >>sys.stderr, "# %d users to process" % max_id
        for account_id in xrange(max_id):
            try:
                account = Account._byID(account_id, data=True)
            except NotFound:
                continue
            
            row = (
                account._id,
                self.utf8(account.name),
                account.email if hasattr(account, 'email') else None,
                account.link_karma,
                account.comment_karma
            )
            table.insert(values=row).execute()
            

    def export_links(self):
        max_id = self.max_thing_id(Link)
        table = Table('articles', self.db, autoload=True)
        print >>sys.stderr, "# %d articles to process" % max_id
        for link_id in xrange(max_id):
            try:
                link = Link._byID(link_id, data=True)
            except NotFound:
                continue
            
            sr = Subreddit._byID(link.sr_id, data=True)
            
            row = (
                link._id,
                self.utf8(link.title),
                self.utf8(link.article),
                link.author_id,
                link._date,
                sr.name
            )
            table.insert(values=row).execute()

    def export_comments(self):
        max_id = self.max_thing_id(Comment)
        table = Table('comments', self.db, autoload=True)
        print >>sys.stderr, "# %d comments to process" % max_id
        for comment_id in xrange(max_id):
            try:
                comment = Comment._byID(comment_id, data=True)
            except NotFound:
                continue
            
            row = (
                comment._id,
                comment.author_id,
                comment.link_id,
                comment.body,
                comment._date
            )
            table.insert(values=row).execute()

    def export_votes(self):
        self.export_rel_votes(Link, 'article_votes')
        self.export_rel_votes(Comment, 'comment_votes')

    def export_rel_votes(self, votes_on_cls, tablename):
        # Vote.vote(c.user, link, action == 'like', request.ip)
        
        rel = Vote.rel(Account, votes_on_cls)
        max_id = self.max_rel_type_id(rel)
        table = Table(tablename, self.db, autoload=True)
        print >>sys.stderr, "# %d votes_on_cls votes to process" % max_id
        for vote_id in xrange(max_id):
            try:
                vote = rel._byID(vote_id, data=True)
            except NotFound:
                continue
            
            row = (
                vote._id,
                vote._thing1_id, # Account
                vote._thing1_id, # Link/Comment (votes_on_cls)
                vote._name, # Vote value
                vote._date
            )
            table.insert(values=row).execute()

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
        Table('users', self.db,
            Column('id', Integer, primary_key=True, index=True),
            Column('name', VARCHAR(), index=True),
            Column('email', VARCHAR()),
            Column('article_karma', Integer),
            Column('comment_karma', Integer),
        ).create()
        
        Table('articles', self.db,
            Column('id', Integer, primary_key=True, index=True),
            Column('title', VARCHAR(), index=True),
            Column('body', TEXT()),
            Column('author_id', Integer, ForeignKey('users.id'), index=True),
            Column('updated_at', DateTime()),
            Column('subreddit', VARCHAR()),
        ).create()

        Table('comments', self.db,
            Column('id', Integer, primary_key=True, index=True),
            Column('author_id', Integer, ForeignKey('users.id'), index=True),
            Column('article_id', Integer, ForeignKey('articles.id'), index=True),
            Column('body', TEXT()),
            Column('updated_at', DateTime()),
        ).create()

        Table('article_votes', self.db,
            Column('id', Integer, primary_key=True, index=True),
            Column('user_id', Integer, ForeignKey('users.id'), index=True),
            Column('article_id', Integer, ForeignKey('articles.id'), index=True),
            Column('vote', Integer()),
            Column('updated_at', DateTime()),
        ).create()

        Table('comment_votes', self.db,
            Column('id', Integer, primary_key=True, index=True),
            Column('user_id', Integer, ForeignKey('users.id'), index=True),
            Column('comment_id', Integer, ForeignKey('comments.id'), index=True),
            Column('vote', Integer()),
            Column('updated_at', DateTime()),
        ).create()
