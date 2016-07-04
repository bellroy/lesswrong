#!/bin/sh -e

[ -z "$1" ] && echo 'Specify destination file path' && exit 1

DESTFILE="$1"
DESTDIR=$(dirname "$DESTFILE")

cd /tmp
curl -O http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
gunzip GeoLiteCity.dat.gz

install -m 755 -d "$DESTDIR"
install -m 644 -T GeoLiteCity.dat "$DESTFILE"
