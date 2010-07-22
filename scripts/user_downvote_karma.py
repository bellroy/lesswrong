from r2.models import Account, Vote
from pylons import g

def user_downvote_karma_count(filename):
    users = Account._query(data=True)
    
    f = open(filename, 'w')
    f.write("Username,Karma,Down Votes\n")
    
    for user in users:
        downvote_count = g.cache.get(user.vote_cache_key())
        if downvote_count is None:
            downvote_count = len(list(Vote._query(Vote.c._thing1_id == user._id,
                                                  Vote.c._name == str(-1))))

        f.write("%s,%d,%d\n" % (user.name, user.safe_karma, downvote_count))

    f.close()
