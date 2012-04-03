# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################
from pylons import c

import cgi
import urllib
import re

import lxml.html
from lxml.html import soupparser
from lxml.html.clean import Cleaner, autolink_html

MD_START = '<div class="md">'
MD_END = '</div>'


# Cleaner is initialised with differences to the defaults
# embedded: We want to allow flash movies in posts
# style: enable removal of style
# safe_attrs_only: need to allow strange arguments to <object>
sanitizer = Cleaner(embedded=False,safe_attrs_only=False)
comment_sanitizer = Cleaner(embedded=False,style=True,safe_attrs_only=False)

def python_websafe(text):
    return text.replace('&', "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def python_websafe_json(text):
    return text.replace('&', "&amp;").replace("<", "&lt;").replace(">", "&gt;")

try:
    from Cfilters import uwebsafe as c_websafe, uspace_compress, \
        uwebsafe_json as c_websafe_json
    def spaceCompress(text):
        try:
            text = unicode(text, 'utf-8')
        except TypeError:
            text = unicode(text)
        return uspace_compress(text)
except ImportError:
    c_websafe      = python_websafe
    c_websafe_json = python_websafe_json
    _between_tags1 = re.compile('> +')
    _between_tags2 = re.compile(' +<')
    _spaces = re.compile('[\s]+')
    _ignore = re.compile('(' + MD_START + '.*?' + MD_END + ')', re.S | re.I)
    def spaceCompress(content):
        res = ''
        for p in _ignore.split(content):
            if not p.startswith(MD_START) and not p.endswith(MD_END):
                p = _spaces.sub(' ', p)
                p = _between_tags1.sub('>', p)
                p = _between_tags2.sub('<', p)
            res += p
        return res

class _Unsafe(unicode): pass

def _force_unicode(text):
    try:
        text = unicode(text, 'utf-8', 'ignore')
    except TypeError:
        text = unicode(text)
    return text

def _force_utf8(text):
    return str(_force_unicode(text).encode('utf8'))

def _force_ascii(text):
    return _force_unicode(text).encode('ascii', 'ignore')

def unsafe(text=''):
    return _Unsafe(_force_unicode(text))

def unsafe_wrap_md(html=''):
    return unsafe(MD_START + html + MD_END)

def websafe_json(text=""):
    return c_websafe_json(_force_unicode(text))

def websafe(text=''):
    if text.__class__ == _Unsafe:
        return text
    elif text.__class__ != unicode:
        text = _force_unicode(text)
    return c_websafe(text)

from mako.filters import url_escape
def edit_comment_filter(text = ''):
    try:
        text = unicode(text, 'utf-8')
    except TypeError:
        text = unicode(text)
    return url_escape(text)

#TODO is this fast?
url_re = re.compile(r"""
    (\[[^\]]*\]:?)?         # optional leading pair of square brackets
    \s*                     # optional whitespace
    (\()?                   # optional open bracket
    (?<![<])                # No angle around link already
    (http://[^\s\'\"\]\)]+) # a http uri
    (?![>])                 # No angle around link already
    (\))?                   # optional close bracket
    """, re.VERBOSE)
jscript_url = re.compile('<a href="(?!http|ftp|mailto|/).*</a>', re.I | re.S)
href_re = re.compile('<a href="([^"]+)"', re.I | re.S)
code_re = re.compile('<code>([^<]+)</code>')
a_re    = re.compile('>([^<]+)</a>')

def wrap_urls(text):
    #wrap urls in "<>" so that markdown will handle them as urls
    matches = url_re.finditer(text)
    def check(match):
        square_brackets, open_bracket, link, close_bracket = match.groups()
        return match if link and not square_brackets else None

    matched = filter(None, [check(match) for match in matches])
    segments = []
    start = 0
    for match in matched:
        segments.extend([text[start:match.start(3)], '<', match.group(3), '>'])
        start = match.end(3)

    # Tack on any trailing bits
    segments.append(text[start:])

    return ''.join(segments)

#TODO markdown should be looked up in batch?
#@memoize('markdown')
def safemarkdown(text, div=True):
    from contrib.markdown import markdown
    if text:
        # increase escaping of &, < and > once
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") 
        text = wrap_urls(text)

        try:
            text = markdown(text)
        except RuntimeError:
            text = "<p><em>Comment Broken</em></p>"
        #wipe malicious javascript
        text = jscript_url.sub('', text)
        def href_handler(m):
            x = m.group(1).replace('&amp;', '&')
            if c.cname:
                return '<a target="_top" href="%s"' % x
            else:
                return '<a href="%s"' % x
        def code_handler(m):
            l = m.group(1)
            return '<code>%s</code>' % l.replace('&amp;','&')
        #unescape double escaping in links
        def inner_a_handler(m):
            l = m.group(1)
            return '>%s</a>' % l.replace('&amp;','&')
        # remove the "&" escaping in urls
        text = href_re.sub(href_handler, text)
        text = code_re.sub(code_handler, text)
        text = a_re.sub(inner_a_handler, text)
        return MD_START + text + MD_END if div else text

def keep_space(text):
    text = websafe(text)
    for i in " \n\r\t":
        text=text.replace(i,'&#%02d;' % ord(i))
    return unsafe(text)

def unkeep_space(text):
    return text.replace('&#32;', ' ').replace('&#10;', '\n').replace('&#09;', '\t')

whitespace_re = re.compile('^\s*$')
def killhtml(html=''):
    html_doc = soupparser.fromstring(remove_control_chars(html))
    text = filter(lambda text: not whitespace_re.match(text), html_doc.itertext())
    cleaned_html = ' '.join([fragment.strip() for fragment in text])
    return cleaned_html

control_chars = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')   # Control characters *except* \t \r \n
def remove_control_chars(text):
    return control_chars.sub('',text)

def cleanhtml(html='', cleaner=None):
    html_doc = soupparser.fromstring(remove_control_chars(html))
    if not cleaner:
        cleaner = sanitizer
    cleaned_html = cleaner.clean_html(html_doc)
    return lxml.html.tostring(autolink_html(cleaned_html))

def clean_comment_html(html=''):
    return cleanhtml(html, comment_sanitizer)

block_tags = r'h1|h2|h3|h4|h5|h6|table|ol|dl|ul|menu|dir|p|pre|center|form|fieldset|select|blockquote|address|div|hr'
linebreaks_re = re.compile(r'(\n{2}|\r{2}|(?:\r\n){2}|</?(?:%s)[^>]*?>)' % block_tags)
tags_re = re.compile(r'</?(?:%s)' % block_tags)
def format_linebreaks(html=''):
    paragraphs = ['<p>%s</p>' % p if not tags_re.match(p) else p
                  for p in linebreaks_re.split(html.strip())
                  if not whitespace_re.match(p)]
    return ''.join(paragraphs)
