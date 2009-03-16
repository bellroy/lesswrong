# -*- coding: utf-8 -*-
import nose

from r2.lib.importer import AtomImporter

import gdata
from gdata import atom

DUMMY_EMAIL = 'test@lesswrong.com'
DUMMY_URI = 'http://www.lesswrong.com/'
ATOM_TYPE = 'application/atom+xml'
HTML_TYPE = 'text/html'
CATEGORY_NS = 'http://www.blogger.com/atom/ns#'
CATEGORY_KIND = 'http://schemas.google.com/g/2005#kind'
POST_KIND = 'http://schemas.google.com/blogger/2008/kind#post'
COMMENT_KIND = 'http://schemas.google.com/blogger/2008/kind#comment'
ATOM_THREADING_NS = 'http://purl.org/syndication/thread/1.0'

class InReplyTo(atom.ExtensionElement):
  """Supplies the in-reply-to element from the Atom threading protocol."""

  def __init__(self, ref, href=None):
    """Constructs an InReplyTo element."""
    attrs = {}
    attrs['ref'] = ref
    attrs['type'] = ATOM_TYPE
    if href:
      attrs['href'] = href
    atom.ExtensionElement.__init__(self, 'in-reply-to',
                                   namespace=ATOM_THREADING_NS,
                                   attributes=attrs)

class AtomFeedFixture(object):

    def __init__(self, title='Feed Fixture', url='http://www.lesswrong.com/.rss', alternate_url='http://www.lesswrong.com/'):
        # Create the top-level feed object
        feed = gdata.GDataFeed()

        # Fill in the feed object with the boilerplate metadata
        feed.generator = atom.Generator(text='Blogger')
        feed.title = atom.Title(text=title)
        feed.link.append(
            atom.Link(href=url, rel='self', link_type=ATOM_TYPE))
        feed.link.append(
            atom.Link(href=alternate_url, rel='alternate', link_type=HTML_TYPE))
        self.feed = feed
        self.ids  = {}

    #TODO Need an author generator: name, email
    def _add_entry(self, entry_id, kind, author='Anonymous', content='', **kw):
        entry = gdata.GDataEntry()
        entry.link.append(
            atom.Link(href=DUMMY_URI, rel='self', link_type=ATOM_TYPE))
        entry.link.append(
            atom.Link(href=DUMMY_URI, rel='alternate', link_type=HTML_TYPE))

        # Add the author
        #author_name = self._Encode(value)
        entry.author = atom.Author(atom.Name(text=author))

        # Add the content
        entry.content = atom.Content(
            content_type='html', text=content)
            # content_type='html', text=self._TranslateContents(tag_contents))

        # Add the kind
        entry.category.append(
            atom.Category(scheme=CATEGORY_KIND, term=kind))

        if kind == COMMENT_KIND:
            # Add the post id to the comment
            entry.extension_elements.append(InReplyTo(kw['post_id']))

        # Add the id of the entry
        entry.id = atom.Id(entry_id)
        self.feed.entry.append(entry)
        return entry_id

    def add_post(self, **kw):
        post_id = self.post_id
        return self._add_entry(post_id, POST_KIND, **kw)

    def add_comment(self, post_id, **kw):
        comment_id = self.comment_id
        return self._add_entry(comment_id, COMMENT_KIND, post_id=post_id, **kw)

    def __getattr__(self, attr):
        if attr.endswith('_id'):
            self.ids[attr] = self.ids.get(attr, 0) + 1
            return "%s-%d" % (attr[:-3], self.ids[attr])
        else:
            raise AttributeError, '%s not found' % attr

    def __str__(self):
        # Return self an an XML atom feed string
        # print str(self.feed)
        return str(self.feed)

class TestAtomImporter(object):

    def test_posts_by_author(self):
        feed = AtomFeedFixture()
        for author in ['Joe Bloggs','Not Joe Bloggs','Joe Bloggs','Someone Else']:
            feed.add_post(author=author)
        importer = AtomImporter(str(feed))
        post_ids = [post.id.text for post in importer.posts_by(['Joe Bloggs'])]
        assert post_ids == ['post-1','post-3']

    def test_posts_by_authors(self):
        feed = AtomFeedFixture()
        for author in ['Joe Bloggs','Steve Jobs','Not Joe Bloggs','Jane Smith','Bill Gates','John Smith','Bill Gates']:
            feed.add_post(author=author)
        importer = AtomImporter(str(feed))
        post_ids = [post.id.text for post in importer.posts_by(['Steve Jobs', 'Bill Gates'])]
        assert post_ids == ['post-2','post-5','post-7']

    def test_comments_on_post(self):
        feed = AtomFeedFixture()
        post1 = feed.add_post()
        comment1 = feed.add_comment(post1)
        post2 = feed.add_post()
        comment2 = feed.add_comment(post2)
        comment3 = feed.add_comment(post1)
        importer = AtomImporter(str(feed))
        comment_ids = [comment.id.text for comment in importer.comments_on_post(post1)]
        assert comment_ids == [comment1, comment3]

    def test_rewrite_urls_in_post_body(self):

        def url_rewriter(match):
            # This replacement will deliberately match again if the importer
            # processes the same url twice 
            return match.group().replace('overcomingbias', 'overcomingbias-rewritten')

        content = (
            ('Some text', 'Some text'),
            ('Blah <a href="http://www.overcomingbias.com/2007/11/passionately-wr.html">Link</a> more',
                'Blah <a href="http://www.overcomingbias-rewritten.com/2007/11/passionately-wr.html">Link</a> more')
        )

        for input_content, expected_content in content:
            feed = AtomFeedFixture()
            post = feed.add_post(content=input_content)
            importer = AtomImporter(str(feed), url_handler=url_rewriter)
            yield self.check_text, importer.get_post(post).content.text, expected_content

    @staticmethod
    def check_text(text, expected_text):
        assert text == expected_text
    
    def test_rewrite_urls_in_comments(self):
        pass

    def test_set_sort_order(self):
        pass
    
    def test_filter_html_in_titles(self):
        pass
    
    def test_set_comment_is_html(self):
        pass
    
    def test_auto_account_creation(self):
        pass
