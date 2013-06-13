from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, \
     CreationError
from r2.lib.utils import base_url, tup, domain, worker, title_to_url, \
     UrlParser, set_last_modified
from account import Account
from subreddit import Subreddit
from printable import Printable
import thing_changes as tc
from r2.config import cache
from r2.lib.memoize import memoize, clear_memo
from r2.lib import utils
from r2.lib.wiki import Wiki
from mako.filters import url_escape
from r2.lib.strings import strings, Score
from r2.lib.db.operators import lower
from r2.lib.db import operators
from r2.lib.filters import _force_unicode
from r2.models.subreddit import FakeSubreddit
from r2.models.image_holder import ImageHolder
from r2.models.poll import containspolls, parsepolls

from pylons import c, g, request
from pylons.i18n import ungettext

import re
import random
import urllib
from datetime import datetime


class Award(Thing, Printable):
    _defaults = dict(reported = 0, 
                     moderator_banned = False,
                     banned_before_moderator = False,
                     is_html = False,
                     retracted = False,
                     show_response_to = False,
                     collapsed = False)

    @staticmethod
    def cache_key(wrapped):
        return False

    @classmethod
    def _new(cls, author, reason, amount, recipient, ip, date = None):
        award = Award(reason = reason,
                      amount = amount,
                      author_id = author._id,
                      recipient_id = recipient._id,
                      ip = ip,
                      date = date)
        award._commit()

    def recipient(self):
        return Account._byID(self.recipient_id, data=True)

    def _commit(self, *a, **kw):

        Thing._commit(self, *a, **kw)

