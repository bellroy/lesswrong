import urllib2, urllib, re
from cookielib import CookieJar
from r2.models import Account

def wiki_user_query(name):
    # WikiMedia requires first character be uppercase, non-special character
    if name[:1].isalnum():
        wikiname = name[:1].upper() + name[1:]
    elif name[:1] == '_':
        return 'undecidable'
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # input-type values from the html form
    formdata = { "list" : "allusers", "aufrom" : wikiname }
    data_encoded = urllib.urlencode(formdata)
    response = opener.open("http://wiki.lesswrong.com/api.php?action=query", data_encoded)
    content = response.read()
    # WikiMedia renders username underscores as spaces
    return wikiname.replace('_', ' ') in content
