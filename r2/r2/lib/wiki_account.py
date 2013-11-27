import urllib2, urllib, re
from pylons import g
from cookielib import CookieJar
from lxml import etree

class WikiError(Exception): pass


def create(name, password, email):
    '''Attempt to create a Less Wrong Wiki account with the given
    username, password and email. Raises a WikiError with the
    error code from MediaWiki if unsuccessful. See
    https://www.mediawiki.org/wiki/API:Account_creation#Possible_errors

    '''
    cj = CookieJar()
    endpoint = g.wiki_api_url + '?action=createaccount'
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # input-type values from the html form
    formdata = { "format": "xml",
                 "name": name,
                 "password": password,
                 "email": email,
                 "language": "en",
                 "token": '' }

    content = opener.open(endpoint, urllib.urlencode(formdata)).read()
    token = etree.fromstring(content).find('.//createaccount').attrib['token']
    formdata['token'] = token
    xml = etree.fromstring(opener.open(endpoint,
                                       urllib.urlencode(formdata)).read())

    if xml.find('createaccount') is None:
        raise WikiError, xml.find('.//error').attrib['code']
    return True

def exists(name):
    '''Check if NAME is a registered account on the LessWrong Wiki.'''
    query = '{0}?action=query&format=xml&list=users&ususers={1}'
    response = urllib2.urlopen(query.format(g.wiki_api_url,
                                            urllib.urlencode(name)))
    if etree.fromstring(response.read()).find('.//user').get('missing') == '':
        return False
    return True

def valid_name(name):
    '''Check if NAME is allowable as a MediaWiki account name. MediaWiki
    will strip leading and trailing underscores and compress multiple
    consecutive underscores into a single space, so we disallow them.

    '''
    if name[0] == '_': return False
    if name[-1] == '_': return False
    if '__' in name: return False
    return True
