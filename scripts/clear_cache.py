from r2.models import Account
from r2.lib.memoize import clear_memo

def clear_account_by_name_cache():
    q = Account._query(Account.c._deleted == (True, False), data = True)
    for account in q:
        name = account.name
        clear_memo('account._by_name', Account, name.lower(), True)
        clear_memo('account._by_name', Account, name.lower(), False)
        print "Cleared cache for %s" % account.name
