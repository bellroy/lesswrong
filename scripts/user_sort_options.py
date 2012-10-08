from copy import copy
from r2.models import Account

# Changes a saved default sort order for the top links page from all to quarter
def user_sort_options():
    pref = 'browse_sort'
    users = Account._query(data=True)
    for user in users:
        print user.name,
        user_prefs = copy(user.sort_options)
        user_pref = user_prefs.get(pref)
        if user_pref and user_pref == 'all':
            user_prefs[pref] = 'quarter'
            user.sort_options = user_prefs
            user._commit()
            print " *"
        else:
            print
