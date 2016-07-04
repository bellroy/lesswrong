#!/bin/sh -e

[ -z "$1" ] && echo 'Specify destination file path' && exit 1

DESTFILE="$1"
DESTDIR=$(dirname "$DESTFILE")

cd /tmp
curl -O http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
curl -O http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.md5
gunzip GeoLite2-City.mmdb.gz
if [ "$(md5sum GeoLite2-City.mmdb | cut -d' ' -f1)" != \
    "$(cat GeoLite2-City.md5)" ]; then
    echo 'GeoIP database MD5 checksum failed.'
    exit 1
fi

rm GeoLite2-City.md5
install -m 755 -d "$DESTDIR"
install -m 644 -T GeoLite2-City.mmdb "$DESTFILE"
