from gdata import atom

import sys
import os
import re

from random import Random
from r2.models import Link,Comment,Account,Subreddit
from r2.lib.db.thing import NotFound

###########################
# Constants
###########################

#BLOGGER_URL = 'http://www.blogger.com/'
#BLOGGER_NS = 'http://www.blogger.com/atom/ns#'
KIND_SCHEME = 'http://schemas.google.com/g/2005#kind'


#YOUTUBE_RE = re.compile('http://www.youtube.com/v/([^&]+)&?.*')
#YOUTUBE_FMT = r'[youtube=http://www.youtube.com/watch?v=\1]'
#GOOGLEVIDEO_RE = re.compile('(http://video.google.com/googleplayer.swf.*)')
#GOOGLEVIDEO_FMT = r'[googlevideo=\1]'
#DAILYMOTION_RE = re.compile('http://www.dailymotion.com/swf/(.*)')
#DAILYMOTION_FMT = r'[dailymotion id=\1]'

MAX_RETRIES = 10

# Constants for the characters to compose a password from.
# Easilty confused characters like I and l, 0 and O are omitted
PASSWORD_NUMBERS='123456789'
PASSWORD_LOWER_CHARS='abcdefghjkmnpqrstuwxz'
PASSWORD_UPPER_CHARS='ABCDEFGHJKMNPQRSTUWXZ'
PASSWORD_OTHER_CHARS='@#$%^&*'
ALL_PASSWORD_CHARS = ''.join([PASSWORD_NUMBERS,PASSWORD_LOWER_CHARS,PASSWORD_UPPER_CHARS,PASSWORD_OTHER_CHARS])


rng = Random()
def generate_password():
    password = []
    for i in range(8):
        password.append(rng.choice(ALL_PASSWORD_CHARS))
    return ''.join(password)

class AtomImporter(object):

    def __init__(self, doc, url_handler=None):
        """Constructs an importer for an Atom (aka Blogger export) file.

        Args:
        doc: The Atom file as a string
        url_handler: A optional URL transformation function that will be 
        called with urls detected in post and comment bodies.
        """

        # Ensure UTF8 chars get through correctly by ensuring we have a
        # compliant UTF8 input doc.
        self.doc = doc.decode('utf-8', 'replace').encode('utf-8')

        # Read the incoming document as a GData Atom feed.
        self.feed = atom.FeedFromString(self.doc)
        
        # Generate a list of all the posts and their comments
        self.posts = {}
        # Stores the id of posts in the order they appear in the feed.
        self.post_order = []
        self.comments = {}
        self.url_handler = url_handler if url_handler else self._default_url_handler
        self.username_mapping = {}
        
        self._scan_feed()

    @staticmethod
    def _default_url_handler(match):
        return match.group()

    def _scan_feed(self):
        for entry in self.feed.entry:
            # Grab the information about the entry kind
            entry_kind = ""
            for category in entry.category:
                if category.scheme == KIND_SCHEME:
                    entry_kind = category.term

                    if entry_kind.endswith("#comment"):
                        # This entry will be a comment, grab the post that it goes to
                        in_reply_to = entry.FindExtensions('in-reply-to')
                        post_id = in_reply_to[0].attributes['ref'] if in_reply_to else None
                        self._rewrite_urls(entry)
                        comments = self.comments.setdefault(post_id, [])
                        comments.append(entry)

                    elif entry_kind.endswith("#post"):
                        # This entry will be a post
                        # posts_map[self._ParsePostId(entry.id.text)] = post_item
                        post_id = entry.id.text
                        self._rewrite_urls(entry)
                        self.post_order.append(post_id) # Assumes a post has a unique id
                        self.posts[post_id] = entry


    # Borrowed from http://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url/163684#163684
    url_re = re.compile(r"""(?:https?|ftp|file)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]""", re.IGNORECASE)
    def _rewrite_urls(self, entry):
        if not entry.content.text:
            return
        entry.content.text = self.url_re.sub(self.url_handler, entry.content.text)

    def get_post(self, post_id):
        """Retrieve a post by its unique id"""
        return self.posts[post_id]

    def posts_by(self, authors):
        for post_id in self.post_order:
            entry = self.posts[post_id]
            for author in entry.author:
                if author.name.text in authors:
                    yield entry
                    break

    def comments_on_post(self, post_id):
        return self.comments.get(post_id)

    def import_into_subreddit(self, sr):
        for post_id in self.post_order:
            post = self.posts[post_id]
            
            # Get the account for this post
            author = post.author[0]
            raise NotImplementedError

    def _find_account_for(self, name, email):
        """Try to find an existing account using derivations of the name"""
        
        try:
            account = self.username_mapping[(name, email)]
        except KeyError:
            candidates = (
                name,
                name.replace(' ', ''),
                name.replace(' ', '_'),
            )
        
            account = None
            for candidate in candidates:
                q = Account._query(
                    Account.c.name == candidate,
                    Account.c.email == email
                )
                accounts = list(q)
                if accounts:
                    account = accounts[0]
                    account._safe_load()
                    break

            # Cache the result for next time
            self.username_mapping[(name, email)] = account

        if not account:
            raise NotFound

        return account

    # def _username_from_name(self, name):
    #     """Convert a name into a username"""
    #     return name.replace(' ', '_')

    def _get_or_create_account(self, name, email):
        try:
            account = self._find_account_for(name, email)
        except NotFound:
            retry = 1 # First retry will by name2
            while True:
                # Create a new account
                retry += 1
                username = "%s%d" % (name, retry)
                try:
                    account = self.author_class.register(username, generate_password(), email)
                except self.account_exists_exception:
                    # This username is taken, generate another, but first limit the retries
                    if retry > MAX_RETRIES:
                        raise Exception('Unable to generate account after %d retries' % retry)
                else:
                    # update cache with the successful account
                    self.username_mapping[(name, email)] = account
                    break
                
                
        return account

########## Mostly ad hoc, investigative stuff from here on

    def show_posts_by(self, authors):
        """Print the titles of the posts by the list of supplied authors"""
        for entry in self.posts_by(authors):
            # print '%s by %s' % (entry.title.text, author.name.text)
            print entry.title.text

    def show_users_with_email(self):
        for comments in self.comments.itervalues():
            for comment in comments:
                author = comment.author[0]
                if author.email:
                    print "%s|%s" % (author.name.text, author.email.text)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print 'Usage: %s <blogger_export_file>' % os.path.basename(sys.argv[0])
        print
        print ' Imports the blogger export file.'
        sys.exit(-1)

    xml_file = open(sys.argv[1])
    xml_doc = xml_file.read()
    xml_file.close()
    importer = AtomImporter(xml_doc)
    xml_doc = None
    #print importer.show_posts_by('Eliezer Yudkowsky')
    importer.show_users_with_email()
