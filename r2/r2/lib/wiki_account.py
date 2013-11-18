import urllib2, urllib, re
from pylons import g
from cookielib import CookieJar
from lxml import etree

def create_wiki_account(name, password, email):
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # input-type values from the html form
    formdata = { "format" : "xml", "name" : name, "password" : password, "email" : email, "language" : "en" }
    data_encoded = urllib.urlencode(formdata)
    response = opener.open("http://{0}/api.php?action=createaccount".format(g.wiki_host), data_encoded)
    content = response.read()
    token = etree.fromstring(content).find("createaccount").attrib["token"]
    formdata2 = { "format" : "xml", "name" : name, "password" : password, "email" : email, "language" : "en", "token" : token }
    data_encoded2 = urllib.urlencode(formdata2)
    response2 = opener.open("http://{0}/api.php?action=createaccount".format(g.wiki_host), data_encoded2)
    return response2.read()

