import sys
import os
import re

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

    # Borrowed from http://stackoverflow.com/questions/161738/what-is-the-best-regular-expression-to-check-if-a-string-is-a-valid-url/163684#163684
#     url_re = re.compile(r"""(?:https?|ftp|file)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]""", re.IGNORECASE)
#     def _rewrite_urls(self, entry):
#         if not entry.content.text:
#             return
#         entry.content.text = self.url_re.sub(self.url_handler, entry.content.text)

    def process_post(self, post):
        account = self._get_or_create_account(post['author'], post['authorEmail'])
        # TODO: do more...

    def import_into_subreddit(self, sr, data):
        for post in data:
            try:
                self.process_post(post)
            except Exception, e:
                # TODO: do more...
                pass

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

    def _get_or_create_account(self, name, email):
        try:
            account = self._find_account_for(name, email)
        except NotFound:
            retry = 1 # First retry will by name2
            name = self._username_from_name(name)
            while True:
                # Create a new account
                retry += 1
                username = "%s%d" % (name, retry)
                try:
                    account = register(username, generate_password(), email)
                except AccountExists:
                    # This username is taken, generate another, but first limit the retries
                    if retry > MAX_RETRIES:
                        raise StandardError('Unable to generate account after %d retries' % (retry - 1))
                else:
                    # update cache with the successful account
                    self.username_mapping[(name, email)] = account
                    break

        return account
