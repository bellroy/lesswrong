from r2.lib.utils import UrlParser

from urllib import urlopen
import os.path, yaml, re
from lxml import etree

def url_for_title(title):
    """Uses the MediaWiki API to get the URL for a wiki page
    with the given title"""
    if title is None:
        return None

    from pylons import g
    cache_key = 'wiki_url_%s' % title
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
        g.cache.set(cache_key, wiki_url, time=3600 * 12)

    return wiki_url

def _get_wiki_data(url):
  """Parse the MediaWiki XML export file into a hash of article sequences
     and cache the result keyed on last modified time of the file"""

  wiki_file_name = 'wiki.lesswrong.xml'
  wiki_file_path = os.path.join('..', 'public', 'files', wiki_file_name)
  #wiki_cache_key = wiki_file_name + 

  #wiki = g.permacache.get(wiki_cache_key)

  # Parse the XML file
  wiki = etree.parse(wiki_file_path)
  return _process_data(wiki, url)
  
def _process_data(wiki_data, url):
  """Algo:
     Find references to this article in the wiki dump, note
     the sequence, index and next prev articles"""

  MEDIAWIKI_NS = 'http://www.mediawiki.org/xml/export-0.3/'
  sequences = {}
  lw_url_re = re.compile(r'\[(http://lesswrong\.com/lw/[^ ]+) [^\]]+\]')

  for page in wiki_data.getroot().iterfind('.//{%s}page' % MEDIAWIKI_NS): # TODO: Change to use iterparse
    # Get the titles
    title = page.findtext('{%s}title' % MEDIAWIKI_NS)

    # See if this page is a sequence page
    sequence_elem = page.xpath("mw:revision[1]/mw:text[contains(., '[[Category:Sequences]]')]", namespaces={'mw': MEDIAWIKI_NS})

    if sequence_elem:
      sequence_elem = sequence_elem[0]
      index = 0
      article_index = None
      articles = []

      # Find all the lesswrong urls
      for match in lw_url_re.finditer(sequence_elem.text):
        article_url = match.group(1)

        # Ensure url ends in slash
        if article_url[-1] != '/':
          article_url += '/'

        if article_url.endswith(url):
          article_index = index

        articles.append(article_url)
        index += 1

      if article_index is not None:
        try:
          next = articles[article_index + 1]
        except IndexError:
          next = None
        prev = articles[article_index - 1] if article_index > 0 else None

        sequences[title] = {
          'title': title,
          'next': next,
          'prev': prev,
          'index': article_index
        }
  return {'sequences': sequences}

