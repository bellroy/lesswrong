from r2.lib.db.thing import Thing
from account import Account
from printable import Printable

from pylons import c, g, request

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

