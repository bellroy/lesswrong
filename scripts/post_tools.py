from r2.models import Account, Link, Subreddit, Vote

def create_about_post():
    user = Account._by_name('Eliezer_Yudkowsky')
    sr = Subreddit._by_name('admin')
    link = Link._submit('About LessWrong', 'TBC', user, sr, '::1', [])

def fix_about_post():
    user = Account._by_name('Eliezer_Yudkowsky')
    l = Link._byID(1, data=True)
    # l = Link._byID(int('1i', 36))
    if l.url.lower() == 'self':
        l.url = l.make_permalink_slow()
        l.is_self = True
        l._commit()
        l.set_url_cache()
    v = Vote.vote(user, l, True, l.ip, False)

def disable_comments_on_post(id36):
    # l = Link._byID(int('10', 36))
    l = Link._byID(int(id36,36), data=True)
    l.comments_enabled = False
    l._commit()

