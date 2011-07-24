from r2.lib.utils import UrlParser

from urllib import urlopen
from r2.lib.filters import _force_ascii
import os, os.path, yaml, re
from lxml import etree

# Wiki is singleton like
# http://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/#c22

class Wiki(object):
  def __new__(cls, *args, **kwargs):
    if not '_the_instance' in cls.__dict__:
      cls._the_instance = object.__new__(cls)
    return cls._the_instance

  def __init__(self):
    self.filename = 'wiki.lesswrong.xml'
    object.__init__(self)

  @property
  def pathname(self):
    return os.path.join('..', 'public', 'files', self.filename)

  @property
  def cache_key(self):
    """Cache key for the wiki data"""
    statinfo = os.stat(self.pathname)
    return (self.filename + str(statinfo.st_mtime)).encode('ascii', 'ignore')

  @property
  def data(self):
    """Returns the data extracted from the wiki export XML file"""
    from pylons import g
    wiki_data = g.permacache.get(self.cache_key)

    if wiki_data is None:
      # Parse the XML file
      wiki_xml = etree.parse(self.pathname)
      wiki_data = self._process_data(wiki_xml)
      g.permacache.set(self.cache_key, wiki_data)

    return wiki_data

  def url_for_title(self, title):
      """Uses the MediaWiki API to get the URL for a wiki page
      with the given title"""
      if title is None:
          return None

      from pylons import g
      cache_key = ('wiki_url_%s' % title).encode('ascii', 'ignore')
      wiki_url = g.cache.get(cache_key)
      if wiki_url is None:
          # http://www.mediawiki.org/wiki/API:Query_-_Properties#info_.2F_in
          api = UrlParser(g.wiki_api_url)
          api.update_query(
              action = 'query',
              titles= title,
              prop = 'info',
              format = 'yaml',
              inprop = 'url'
          )

          try:
              response = urlopen(api.unparse()).read()
              parsed_response = yaml.load(response, Loader=yaml.CLoader)
              page = parsed_response['query']['pages'][0]
          except:
              return None

          wiki_url = page.get('fullurl').strip()

          # Things are created every couple of days so 12 hours seems
          # to be a reasonable cache time
          g.permacache.set(cache_key, wiki_url, time=3600 * 12)

      return wiki_url

  def sequences_for_article_url(self, url):
    """Return the article sequences extracted from the wiki export"""
    if url is None:
        return {}

    from pylons import g
    all_sequences = self.data['sequences']
    url = UrlParser(url)
    cache_key = _force_ascii(self.cache_key + url.path)

    sequences = g.permacache.get(cache_key)

    if sequences is None:
      sequences = {}
      for sequence in all_sequences:
        articles = sequence['articles']

        # Find the index of the given URL in the sequence's articles
        try:
          article_index = articles.index(url.path)
        except ValueError:
          article_index = None

        if article_index is not None:
          # The url passed is a part of the current sequence
          try:
            next_in_seq = articles[article_index + 1]
          except IndexError:
            next_in_seq = None
          prev_in_seq = articles[article_index - 1] if article_index > 0 else None

          # Add the result
          title = sequence['title']
          sequences[title] = {
            'title': title,
            'next': next_in_seq,
            'prev': prev_in_seq,
            'index': article_index
          }
      g.permacache.set(cache_key, sequences)

    return sequences

  def _process_data(self, wiki_xml):
    """This method processes the wiki data and extracts what is used"""
    MEDIAWIKI_NS = 'http://www.mediawiki.org/xml/export-0.3/'
    sequences = []
    lw_url_re = re.compile(r'\[(http://lesswrong\.com/lw/[^ ]+) [^\]]+\]')

    for page in wiki_xml.getroot().iterfind('.//{%s}page' % MEDIAWIKI_NS): # TODO: Change to use iterparse
      # Get the titles
      title = page.findtext('{%s}title' % MEDIAWIKI_NS)

      # See if this page is a sequence page
      sequence_elem = page.xpath("mw:revision[1]/mw:text[contains(., '[[Category:Sequences]]')]", namespaces={'mw': MEDIAWIKI_NS})

      if sequence_elem:
        sequence_elem = sequence_elem[0]
        articles = []

        # Find all the lesswrong urls
        for match in lw_url_re.finditer(sequence_elem.text):
          article_url = UrlParser(match.group(1))

          # Only store the path to the article
          article_path = article_url.path

          # Ensure path ends in slash
          if article_path[-1] != '/':
            article_path += '/'

          articles.append(article_path)

        sequences.append({
          'title': title,
          'articles': articles
        })
    return {'sequences': sequences}
