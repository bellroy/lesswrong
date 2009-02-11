from r2.models import Subreddit, Account

def create_as_user_named(username):
    categories = {
        'academia': 'Academia',
        # 'ads': 'Ads',
        # 'age': 'Age',
        'ai': 'Ai',
        'arts': 'Arts',
        'bayesian': 'Bayesian',
        # 'charity': 'Charity',
        # 'currentaffairs': 'Current Affairs',
        'disagreement': 'Disagreement',
        # 'disaster': 'Disaster',
        # 'epistemology': 'Epistemology',
        # 'fiction': 'Fiction',
        # 'finance': 'Finance',
        'future': 'Future',
        # 'gender': 'Gender',
        # 'humor': 'Humor',
        # 'hypocrisy': 'Hypocrisy',
        # 'innovation': 'Innovation',
        'law': 'Law',
        'mating': 'Mating',
        'media': 'Media',
        'medicine': 'Medicine',
        'meta': 'Meta',
        'morality': 'Morality',
        # 'music': 'Music',
        # 'naturalism': 'Naturalism',
        # 'openthread': 'Open Thread',
        'overconfidence': 'Overconfidence',
        # 'personal': 'Personal',
        'philosophy': 'Philosophy',
        'politics': 'Politics',
        'predictionmarkets': 'Prediction markets',
        'psychology': 'Psychology',
        # 'reductionism': 'Reductionism',
        # 'regulation': 'Regulation',
        'religion': 'Religion',
        'science': 'Science',
        'selfdeception': 'Self-deception',
        # 'signaling': 'Signaling',
        # 'socialscience': 'Social science',
        # 'sports': 'Sports',
        'standardbiases': 'Standard biases',
        'statistics': 'Statistics',
        # 'status': 'Status',
        # 'war': 'War',
        # 'webtech': 'Web/tech',
    }

    kw = {
        'lang': 'en',
        'over_18': False,
        'show_media': False,
        'type': 'public',
        'default_listing': 'hot',
    }

    user = Account._by_name(username)

    for name, title in categories.iteritems():
        kw['title'] = title
        sr = Subreddit._create_and_subscribe(name, user, kw)
        print "Created " + name
