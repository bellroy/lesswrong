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
    formdata = { "format" : "xml", "list" : "allusers", "aufrom" : wikiname }
    data_encoded = urllib.urlencode(formdata)
    try:
        response = opener.open(g.wiki_url + "api.php?action=query", data_encoded)
    except (urllib2.URLError, urllib2.HTTPError):
        return 'unknown'
    content = response.read()
    resultxml = etree.fromstring(content)
    # special characters can make the name requested not be the first in the list
    users = [ u.attrib["name"] for u in resultxml.iterfind(".//u") ]
    # WikiMedia renders username underscores as spaces
    if wikiname.replace('_', ' ') in users:
        return 'associated'
    else:
        return 'unassociated'
