import sys
import os
import re
import datetime

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

class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)

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

    # Borrowed from http://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url/163684#163684
#     url_re = re.compile(r"""(?:https?|ftp|file)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]""", re.IGNORECASE)
#     def _rewrite_urls(self, entry):
#         if not entry.content.text:
#             return
#         entry.content.text = self.url_re.sub(self.url_handler, entry.content.text)

    kill_tags_re = re.compile(r'</?[iub]>')
    transform_categories_re = re.compile(r'[- ]')

    def process_post(self, post_data, sr):
        account = self._get_or_create_account(post_data['author'], post_data['authorEmail'])

        title = self.kill_tags_re.sub('', post_data['title'])

        article = u'%s%s' % (post_data['description'],
                             Link._more_marker + post_data['mt_text_more'] if post_data['mt_text_more'] else u'')

        tags = [self.transform_categories_re.sub('_', tag.lower()) for tag in post_data['category']]

        date = datetime.datetime.strptime(post_data['dateCreated'], '%m/%d/%Y %I:%M:%S %p').replace(tzinfo=UTC())

        post = Link._submit(title, article, account, sr, '127.0.0.1', tags, date=date)

        post.comments_enabled = False
        post.blessed = True
        post._commit()

    def import_into_subreddit(self, sr, data):
        for post_data in data:
            try:
                self.process_post(post_data, sr)
            except Exception, e:
                print 'Unable to create post:\n%s\n%s' % (e, post_data)

    def _username_from_name(self, name):
        """Convert a name into a username"""
        return name.replace(' ', '_')

    def _find_account_for(self, name, email):
        """Try to find an existing account using derivations of the name"""

        try:
            account = self.username_mapping[(name, email)]
        except KeyError:
            candidates = (
                name,
                name.replace(' ', ''),
                self._username_from_name(name),
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
