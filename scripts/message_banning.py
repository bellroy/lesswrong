from r2.models import Account

def ban():
    user = #place name of user here
    banned = list(Account._query(Account.c.name == user))[0]
    banned.messagebanned = True
    banned._commit()
