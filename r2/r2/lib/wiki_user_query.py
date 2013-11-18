import urllib2, urllib, re
from pylons import g
from cookielib import CookieJar
from r2.models import Account
from lxml import etree

def wiki_user_query(name):
    """Lesswrong allows usernames to be composed of letters, upper and lowercase,
       numbers, dashes and underscores.  Wikimedia requires the first letter to be
       uppercase and removes leading underscores.  Case one deals with letters and
       numbers, case 2 with underscores and case 3 with dashes"""
    if name[:1].isalnum():
        wikiname = name[:1].upper() + name[1:]
    elif name[:1] == '_':
        return 'undecidable'
    else:
        wikiname = name
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # input-type values from the html form
    formdata = { "format" : "xml", "list" : "users", "ususers" : wikiname }
    data_encoded = urllib.urlencode(formdata)
    try:
        response = opener.open("http://{0}/api.php?action=query".format(g.wiki_url), data_encoded)
    except (urllib2.URLError, urllib2.HTTPError):
        return 'unknown'
    content = response.read()
    resultxml = etree.fromstring(content)
    if resultxml.find(".//user").get("missing") == None:
        return 'associated'
    else:
        return 'unassociated'
