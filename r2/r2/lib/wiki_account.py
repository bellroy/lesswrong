import urllib2, urllib, re
from cookielib import CookieJar

tokenmatcher = re.compile('<\?xml version=\"1.0\"\?><api><createaccount token=\"(.*?)\" result=\"needtoken\" /></api>')

def create_wiki_account(name, password, email):
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # input-type values from the html form
    formdata = { "format" : "xml", "name" : name, "password" : password, "email" : email, "language" : "en" }
    data_encoded = urllib.urlencode(formdata)
    response = opener.open("http://127.0.1.1/mediawiki-1.21.1/api.php?action=createaccount", data_encoded)
    content = response.read()
    print content
    temp = tokenmatcher.match(content)
    token = temp.group(1)
    formdata2 = { "format" : "xml", "name" : name, "password" : password, "email" : email, "language" : "en", "token" : token }
    data_encoded2 = urllib.urlencode(formdata2)
    response2 = opener.open("http://127.0.1.1/mediawiki-1.21.1/api.php?action=createaccount", data_encoded2)
    content2 = response2.read()
    return content2
    print 'result="success"' in content2
    print content2
