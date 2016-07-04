#!/bin/sh -e

[ -z "$1" ] && echo 'Specify destination file path' && exit 1

DESTFILE="$1"
DESTDIR=$(dirname "$DESTFILE")

cd /tmp
curl -O https://wiki.lesswrong.com/wiki.lesswrong.xml.gz
gunzip wiki.lesswrong.xml.gz
install -o vagrant -m 644 wiki.lesswrong.xml "$DESTFILE"
