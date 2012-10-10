# A one-time script to find all users with textual locations, and add
# corresponding latitude/longitude info to the database.


import json
import urllib, urllib2

from pylons import g

from r2.models import Account


def geolocate_users():
    users = list(Account._query(Account.c.pref_location != None,
                                data=True))
    log('Geolocating {0} users...'.format(len(users)))

    for user in users:
        if not user.pref_location or user.pref_latitude:
            continue
        coords = geolocate_address(user.pref_location)
        if coords:
            user.pref_latitude, user.pref_longitude = coords
            user._commit()
            log('{0} ({1!r}) => ({2:.3}, {3:.3})'.format(
                user.name, user.pref_location, user.pref_latitude, user.pref_longitude))


def geolocate_address(addr):
    base = 'http://maps.googleapis.com/maps/api/geocode/json?'
    url = base + urllib.urlencode({'sensor': 'false', 'address': addr})
    sock = urllib2.urlopen(url)
    try:
        raw = sock.read()
    finally:
        sock.close()

    try:
        data = json.loads(raw)
        if data['status'] != 'OK':
            log('Error geolocating {0!r} - {1}'.format(addr, data['status']))
            return None

        coords = data['results'][0]['geometry']['location']
        return coords['lat'], coords['lng']
    except Exception:
        log('Malformed response for address {0!r}'.format(addr))
        return None


def log(msg):
    print(msg)


geolocate_users()
