from r2.models import Account, PendingJob

users = list(Account._query())
for user in users:
    if hasattr(user, 'email'):
        data = {'name' : user.name, 'password' : None, 'email' : user.email, 'attempt' : 0}
        PendingJob.store(None, 'create_wiki_account', data)
