from gdata import atom

import sys
import os

# from r2.models import Link,Comment,Account,Subreddit

###########################
# Constants
###########################

#BLOGGER_URL = 'http://www.blogger.com/'
#BLOGGER_NS = 'http://www.blogger.com/atom/ns#'
KIND_SCHEME = 'http://schemas.google.com/g/2005#kind'

#YOUTUBE_RE = re.compile('http://www.youtube.com/v/([^&]+)&?.*')
#YOUTUBE_FMT = r'[youtube=http://www.youtube.com/watch?v=\1]'
#GOOGLEVIDEO_RE = re.compile('(http://video.google.com/googleplayer.swf.*)')
#GOOGLEVIDEO_FMT = r'[googlevideo=\1]'
#DAILYMOTION_RE = re.compile('http://www.dailymotion.com/swf/(.*)')
#DAILYMOTION_FMT = r'[dailymotion id=\1]'

class AtomImporter(object):

    def __init__(self, doc):
        """Constructs an importer for an Atom (aka Blogger export) file.

        Args:
        doc: The Atom file as a string
        """

        # Ensure UTF8 chars get through correctly by ensuring we have a
        # compliant UTF8 input doc.
        self.doc = doc.decode('utf-8', 'replace').encode('utf-8')

        # Read the incoming document as a GData Atom feed.
        self.feed = atom.FeedFromString(self.doc)
        
        # Generate a list of all the posts and their comments
        self.posts = []
        self.comments = {}
        self._scan_feed()

    def _scan_feed(self):
        for entry in self.feed.entry:
            # Grab the information about the entry kind
            entry_kind = ""
            for category in entry.category:
                if category.scheme == KIND_SCHEME:
                    entry_kind = category.term

                    if entry_kind.endswith("#comment"):
                        # This entry will be a comment, grab the post that it goes to
                        in_reply_to = entry.FindExtensions('in-reply-to')
                        post_id = in_reply_to[0].attributes['ref'] if in_reply_to else None
                        comments = self.comments.setdefault(post_id, [])
                        comments.append(entry)

                    elif entry_kind.endswith("#post"):
                        # This entry will be a post
                        # posts_map[self._ParsePostId(entry.id.text)] = post_item
                        self.posts.append(entry)

    def posts_by(self, authors):
        for entry in self.posts:
            for author in entry.author:
                if author.name.text in authors:
                    yield entry
                    break

    def comments_on_post(self, post_id):
        return self.comments.get(post_id)

    def show_posts_by(self, authors):
        """Print the titles of the posts by the list of supplied authors"""
        for entry in self.posts_by(authors):
            # print '%s by %s' % (entry.title.text, author.name.text)
            print entry.title.text

if __name__ == '__main__':
  if len(sys.argv) <= 1:
    print 'Usage: %s <blogger_export_file>' % os.path.basename(sys.argv[0])
    print
    print ' Imports the blogger export file.'
    sys.exit(-1)

  xml_file = open(sys.argv[1])
  xml_doc = xml_file.read()
  xml_file.close()
  importer = AtomImporter(xml_doc)
  xml_doc = None
  print importer.show_posts_by('Eliezer Yudkowsky')
