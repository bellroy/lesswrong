from r2.lib import emailer
from r2.models import Account


def get_users_to_notify_for_meetup(coords):
    # This query could definitely be optimized, but I don't expect it to be
    # run too often, so it's probably not worth the effort.
    users = Account._query(
        Account.c.pref_meetup_notify_enabled == True,
        Account.c.email != None,
        Account.c.pref_latitude != None,
        Account.c.pref_longitude != None)
    users = filter(lambda u: u.is_within_radius(coords, u.pref_meetup_notify_radius), users)
    return list(users)


def email_user_about_meetup(user, meetup):
    if meetup.author_id != user._id and user.email:
        emailer.meetup_email(user=user, meetup=meetup)

def email_user_about_repost(user, pendingjob):
    emailer.repost_email(user=user, pendingjob = pendingjob)
