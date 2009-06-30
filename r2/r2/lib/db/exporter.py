import sys
import csv
import os.path
import sqlalchemy as sa

from r2.lib.db import tdb_sql as tdb
from r2.lib.db.thing import NotFound, Relation
from r2.models import Link, Comment, Account, Vote, Subreddit

class Exporter:
    
    def __init__(self, output_dir):
        """Initialise with output directory name"""
        self.output_dir = output_dir

    def export_db(self):
        self.export_users()
        self.export_links()
        self.export_comments()
        self.export_votes()

    def export_users(self):
        max_id = self.max_thing_id(Account)
        writer = self.csv_writer('users')
        print >>sys.stderr, "# %d users to process" % max_id
        for account_id in xrange(max_id):
            try:
                account = Account._byID(account_id, data=True)
            except NotFound:
                continue
            
            row = [
                account._id,
                self.utf8(account.name),
                account.email if hasattr(account, 'email') else None,
                account.link_karma,
                account.comment_karma
            ]
            writer.writerow(row)

    def export_links(self):
        max_id = self.max_thing_id(Link)
        writer = self.csv_writer('articles')
        print >>sys.stderr, "# %d articles to process" % max_id
        for link_id in xrange(max_id):
            try:
                link = Link._byID(link_id, data=True)
            except NotFound:
                continue
            
            sr = Subreddit._byID(link.sr_id, data=True)
            
            row = [
                link._id,
                self.utf8(link.title),
                self.utf8(link.article),
                link.author_id,
                link._date,
                sr.name
            ]
            writer.writerow(row)

    def export_comments(self):
        max_id = self.max_thing_id(Comment)
        writer = self.csv_writer('comments')
        print >>sys.stderr, "# %d comments to process" % max_id
        for comment_id in xrange(max_id):
            try:
                comment = Comment._byID(comment_id, data=True)
            except NotFound:
                continue
            
            row = [
                comment._id,
                comment.author_id,
                comment.body,
                comment._date
            ]
            writer.writerow(row)

    def export_votes(self):
        self.export_rel_votes(Link, 'article_votes')
        self.export_rel_votes(Comment, 'comment_votes')

    def export_rel_votes(self, votes_on_cls, filename):
        # Vote.vote(c.user, link, action == 'like', request.ip)
        
        rel = Vote.rel(Account, votes_on_cls)
        max_id = self.max_rel_type_id(rel)
        writer = self.csv_writer(filename)
        print >>sys.stderr, "# %d votes_on_cls votes to process" % max_id
        for vote_id in xrange(max_id):
            try:
                vote = rel._byID(vote_id, data=True)
            except NotFound:
                continue
            
            row = [
                vote._id,
                vote._thing1_id, # Account
                vote._thing1_id, # Link/Comment (votes_on_cls)
                vote._name, # Vote value
                vote._date
            ]
            writer.writerow(row)

    def max_rel_type_id(self, rel_thing):
        thing_type = tdb.rel_types_id[rel_thing._type_id]
        thing_tbl = thing_type.rel_table[0]
        rows = sa.select([sa.func.max(thing_tbl.c.rel_id)]).execute().fetchall()
        return rows[0][0]

    def max_thing_id(self, thing):
        thing_type = tdb.types_id[thing._type_id]
        thing_tbl = thing_type.thing_table
        rows = sa.select([sa.func.max(thing_tbl.c.thing_id)]).execute().fetchall()
        return rows[0][0]

    def csv_writer(self, type_name):
        filename = os.path.join(self.output_dir, type_name + '.csv')
        return csv.writer(open(filename, 'wb'), quoting=csv.QUOTE_ALL)

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
