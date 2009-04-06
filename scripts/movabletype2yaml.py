#!/usr/bin/env python

# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
import logging
import re
import sys
import time


import yaml

# Derived from code at:
# http://code.google.com/p/google-blog-converters-appengine/
__author__ = 'Wesley Moore'

########################
# Constants
########################

CATEGORY_NS = 'http://www.blogger.com/atom/ns#'
CATEGORY_KIND = 'http://schemas.google.com/g/2005#kind'
POST_KIND = 'http://schemas.google.com/blogger/2008/kind#post'
COMMENT_KIND = 'http://schemas.google.com/blogger/2008/kind#comment'
ATOM_TYPE = 'application/atom+xml'
HTML_TYPE = 'text/html'
ATOM_THREADING_NS = 'http://purl.org/syndication/thread/1.0'
DUMMY_URI = 'http://www.blogger.com/'


###########################
# Translation class
###########################

class MovableType2Yaml(object):
  """Performs the translation of MovableType text export to YAML
  """

  def __init__(self):
    self.next_id = 1
  
  def Translate(self, infile, outfile):
    """Performs the actual translation to YAML.

    Args:
      infile: The input MovableType export file
      outfile: The output file that should receive the translated document
    """
    # Create the top-level feed object
    feed = []
    comments = []

    # Calculate the last updated time by inspecting all of the posts
    last_updated = 0

    # These three variables keep the state as we parse the file
    post_entry = {}    # The current post atom.Entry to populate
    comment_entry = {} # The current comment atom.Entry to populate
    last_entry = None    # The previous post atom.Entry if exists
    tag_name = None      # The current name of multi-line values
    tag_contents = ''    # The contents of multi-line values

    # Loop through the text lines looking for key/value pairs
    split_re = re.compile('^[A-Z ]+:')
    for line in infile:

      # Remove whitespace
      line = line.strip()

      # Check for the post ending token
      if line == '-' * 8 and tag_name != 'BODY':
        if post_entry:
          # Add the post to our feed
          sys.stderr.write("Adding post %s\n" % post_entry['title'])
          feed.insert(0, post_entry)
          last_entry = post_entry

        # Reset the state variables
        post_entry = {}
        comment_entry = {}
        tag_name = None
        tag_contents = ''
        continue

      # Check for the tag ending separator
      elif line == '-' * 5:
        # Get the contents of the body and set the entry contents
        if tag_name == 'BODY':
          post_entry['description'] = self._Encode(tag_contents)

        # This is the start of the COMMENT section.  Create a new entry for
        # the comment and add a link to the original post.
        elif tag_name == 'COMMENT':
          comment_entry['body'] = self._Encode(tag_contents)
          post_entry.setdefault('comments', []).append(comment_entry)
          comment_entry = {}

        # Get the contents of the extended body
        elif tag_name == 'EXTENDED BODY':
          if post_entry:
            post_entry['mt_text_more'] = self._Encode(tag_contents)
          elif last_entry:
            last_entry['mt_text_more'] = self._Encode(tag_contents)

        # Convert any keywords (comma separated values) into Blogger labels
        elif tag_name == 'KEYWORDS':
          post_entry['mt_keywords'] = tag_contents

        # Reset the current tag and its contents
        tag_name = None
        tag_contents = ''
        continue

      # Split the line into key/value pairs
      key = line
      value = ''
      if split_re.match(line):
        elems = line.split(':')
        key = elems[0]
        if len(elems) > 1:
          value = ':'.join(elems[1:]).strip()

      # The author key indicates the start of a post as well as the author of
      # the post entry or comment
      if key == 'AUTHOR':
        # Create a new entry 
        entry = {}

        # Add the author's name
        author_name = self._Encode(value)
        if not author_name:
          author_name = 'Anonymous'
        entry['author'] = author_name

        # Add the appropriate kind, either a post or a comment
        if tag_name == 'COMMENT':
          entry['postid'] = post_entry['postid']
          comment_entry = entry
        else:
          entry['postid'] = 'post-' + self._GetNextId()
          post_entry = entry

      # The title only applies to new posts
      elif key == 'TITLE' and tag_name != 'PING':
        post_entry['title'] = self._Encode(value)

      # If the status is a draft, mark it as so in the entry.  If the status
      # is 'Published' there's nothing to do here
      elif key == 'STATUS':
        post_entry['status'] = value

      # Turn categories into labels
      elif key == 'CATEGORY':
        post_entry.setdefault('category', []).append(value)

      # Convert the date and specify it as the published/updated time
      elif key == 'DATE' and tag_name != 'PING':
        entry = post_entry
        if tag_name == 'COMMENT':
          entry = comment_entry
        entry['dateCreated'] = value

        # Check to see if this was the last post published (so far)
        # seconds = time.mktime(time_val)
        # last_updated = max(seconds, last_updated)

      # Convert all tags into Blogger labels
      elif key == 'TAGS':
        post_entry.setdefault('tags', []).append(value)

      # Update the author's email if it is present and not empty
      elif tag_name == 'COMMENT' and key == 'EMAIL':
        comment_entry['authorEmail'] = value

      # Update the author's URI if it is present and not empty
      elif tag_name == 'COMMENT' and key == 'URL':
        comment_entry['authorUrl'] = value

      # If any of these keys are used, they contain information beyond this key
      # on following lines
      elif key in ('COMMENT', 'BODY', 'EXTENDED BODY', 'EXCERPT', 'KEYWORDS', 'PING'):
        tag_name = key

      # These lines can be safely ignored
      elif key in ('BASENAME', 'ALLOW COMMENTS', 'CONVERT BREAKS', 
                   'ALLOW PINGS', 'PRIMARY CATEGORY', 'IP', 'URL', 'EMAIL'):
        continue

      # If the line is empty and we're processing the body, add a line break
      elif (tag_name == 'BODY' or tag_name == 'EXTENDED BODY' or tag_name == 'COMMENT') and len(line) == 0:
        tag_contents += '\n'

      # This would be a line of content beyond a key/value pair
      elif len(key) != 0:
        tag_contents += line + '\n'


    # Update the feed with the last updated time
    # feed.updated = atom.Updated(self._ToBlogTime(time.gmtime(last_updated)))

    # Serialize the feed object
    yaml.dump(feed, outfile, Dumper=yaml.CDumper)

  def _GetNextId(self):
    """Returns the next entry identifier as a string."""
    ret = self.next_id
    self.next_id += 1
    return str(self.next_id)

  def _CreateSnippet(self, content):
    """Creates a snippet of content.  The maximum size being 53 characters,
    50 characters of data followed by elipses.
    """
    content = re.sub('</?[^>/]+/?>', '', content)
    if len(content) < 50:
      return content
    return content[0:49] + '...'

  def _TranslateContents(self, content):
    #content = content.replace('\n', '<br/>')
    return self._Encode(content)

  def _Encode(self, content):
    return content.decode('utf-8', 'replace').encode('utf-8')

  def _FromMtTime(self, mt_time):
    return time.strptime(mt_time, "%m/%d/%Y %I:%M:%S %p")

  def _ToBlogTime(self, time_tuple):
    """Converts a time struct to a Blogger time/date string."""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time_tuple)

if __name__ == '__main__':
  if len(sys.argv) <= 1:
    print 'Usage: %s <movabletype_export_file>' % os.path.basename(sys.argv[0])
    print
    print ' Outputs the converted file to standard out.'
    sys.exit(-1)
    
  mt_file = open(sys.argv[1])
  translator = MovableType2Yaml()
  translator.Translate(mt_file, sys.stdout)
  mt_file.close()

    
