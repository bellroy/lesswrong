#!/usr/bin/env python

import sys
import re

def main():
    infilename, outfilename = sys.argv[1:3]

    infile = open(infilename)
    buf = infile.read()
    buf = buf.decode('utf-8')

    re_invalid_dashes = re.compile(ur'^-----(---)?(\r)?\n(?!--------|BODY:|EXTENDED BODY:|EXCERPT:|KEYWORDS:|AUTHOR:|COMMENT:|PING:|\Z)', re.MULTILINE)
    buf = re_invalid_dashes.sub(ur'----\n', buf)

    re_control_chars = re.compile(ur'(\s)[]')
    buf = re_control_chars.sub(ur'\1', buf)
    re_control_chars = re.compile(ur'[](\s)')
    buf = re_control_chars.sub(ur'\1', buf)
    re_control_chars = re.compile(ur'[]')
    buf = re_control_chars.sub(ur' ', buf)

    buf = buf.encode('utf-8')
    outfile = open(outfilename, 'w')
    outfile.write(buf)

if __name__ == '__main__':
    main()
