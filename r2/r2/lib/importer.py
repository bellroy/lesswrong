import sys
import os
import re
import datetime
import pytz
import yaml

from random import Random
from r2.models import Link,Comment,Account,Subreddit
from r2.models.account import AccountExists, register
from r2.lib.db.thing import NotFound

###########################
# Constants
###########################

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

class Importer(object):

    def __init__(self, url_handler=None):
        """Constructs an importer that takes a data structure based on a yaml file.

        Args:
        url_handler: A optional URL transformation function that will be
        called with urls detected in post and comment bodies.
        """

        self.url_handler = url_handler if url_handler else self._default_url_handler

        self.username_mapping = {}

    @staticmethod
    def _default_url_handler(match):
        return match.group()

    def process_comment(self, comment_data, post):
        account = self._get_or_create_account(comment_data['author'], comment_data['authorEmail'])

        date = datetime.datetime.strptime(comment_data['dateCreated'], '%m/%d/%Y %I:%M:%S %p').replace(tzinfo=pytz.timezone('UTC'))

        comment, inbox_rel = Comment._new(account, post, None, comment_data['body'], '127.0.0.1', date=date)

        comment.is_html = True
        comment.ob_imported = True
        comment._commit()


    kill_tags_re = re.compile(r'</?[iub]>')
    transform_categories_re = re.compile(r'[- ]')

    def process_post(self, post_data, sr):
        account = self._get_or_create_account(post_data['author'], post_data['authorEmail'])

        title = self.kill_tags_re.sub('', post_data['title'])

        article = u'%s%s' % (post_data['description'],
                             Link._more_marker + post_data['mt_text_more'] if post_data['mt_text_more'] else u'')

        tags = [self.transform_categories_re.sub('_', tag.lower()) for tag in post_data['category']]

        date = datetime.datetime.strptime(post_data['dateCreated'], '%m/%d/%Y %I:%M:%S %p').replace(tzinfo=pytz.timezone('UTC'))

        post = Link._submit(title, article, account, sr, '127.0.0.1', tags, date=date)

        post.blessed = True
        post.comment_sort_order = 'old'
        post.ob_permalink = post_data['permalink']
        post._commit()

        [self.process_comment(comment_data, post) for comment_data in post_data.get('comments', [])]

    def substitute_ob_url(self, url):
        try:
            url = self.post_mapping[url]
        except KeyError:
            pass
        return url

    # Borrowed from http://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url/163684#163684
    url_re = re.compile(r"""(?:https?|ftp|file)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]""", re.IGNORECASE)
    def rewrite_ob_urls(self, text):
        if text:
            text = self.url_re.sub(lambda match: self.substitute_ob_url(match.group()), text)

        return text

    def post_process_post(self, post):
        """Perform post processsing to rewrite URLs and generate mapping
           between old and new permalinks"""
        post.article = self.rewrite_ob_urls(post.article)
        comments = Comment._query(Comment.c.link_id == post._id, data = True)
        for comment in comments:
            comment.body = self.rewrite_ob_urls(comment.body)

    def import_into_subreddit(self, sr, data):
        mapping_file = open('import_mapping.yml', 'w')

        for post_data in data:
            try:
                self.process_post(post_data, sr)
            except Exception, e:
                print 'Unable to create post:\n%s\n%s\n%s' % (type(e), e, post_data)

        posts = list(Link._query(Link.c.ob_permalink != None, data = True))

        # Generate a mapping between old and new posts
        self.post_mapping = {}
        for post in posts:
            self.post_mapping[post.ob_permalink] = post.url

        # Write out the permalink mapping
        yaml.dump(self.post_mapping, mapping_file, Dumper=yaml.CDumper)

        # Update URLs in the posts and comments
        for post in posts:
            self.post_process_post(post)

    def _username_from_name(self, name):
        """Convert a name into a username"""
        return name.replace(' ', '_')

    def _query_account(self, *args):
        account = None
        kwargs = {'data': True}
        q = Account._query(*args, **kwargs)
        accounts = list(q)
        if accounts:
            account = accounts[0]
        return account

    def _find_account_for(self, name, email):
        """Try to find an existing account using derivations of the name"""

        try:
            # Look for an account we have cached
            account = self.username_mapping[(name, email)]
        except KeyError:
            # Look for an existing account that was created due to a previous import
            account = self._query_account(Account.c.ob_account_name == name,
                                          Account.c.email == email)
            if not account:
                # Look for an existing account based on derivations of the name
                candidates = (
                    name,
                    name.replace(' ', ''),
                    self._username_from_name(name)
                )

                account = None
                for candidate in candidates:
                    account = self._query_account(Account.c.name == candidate,
                                                  Account.c.email == email)
                    if account:
                        account.ob_account_name = name
                        account._commit()
                        break

            # Cache the result for next time
            self.username_mapping[(name, email)] = account

        if not account:
            raise NotFound

        return account

    def _get_or_create_account(self, full_name, email):
        try:
            account = self._find_account_for(full_name, email)
        except NotFound:
            retry = 2 # First retry will by name2
            name = self._username_from_name(full_name)
            username = name
            while True:
                # Create a new account
                try:
                    account = register(username, generate_password(), email)
                    account.ob_account_name = full_name
                    account._commit()
                except AccountExists:
                    # This username is taken, generate another, but first limit the retries
                    if retry > MAX_RETRIES:
                        raise StandardError("Unable to create account for '%s' after %d attempts" % (full_name, retry - 1))
                else:
                    # update cache with the successful account
                    self.username_mapping[(full_name, email)] = account
                    break
                username = "%s%d" % (name, retry)
                retry += 1

        return account
