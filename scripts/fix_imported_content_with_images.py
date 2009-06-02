import urlparse
import re

def print_change(old, new):
    print "  %s => %s" % (old, new)

interesting_hosts = set(['www.overcomingbias.com', 'robinhanson.typepad.com'])
funny_imgs     = {
    'http://robinhanson.typepad.com/.a/6a00d8341c6a2c53ef010536c21d63970b-800wi': 'http://lesswrong.com/static/imported/6a00d8341c6a2c53ef010536c21d63970b-800wi.jpg',
}
ext_re = re.compile(r'.*\.(jpg|gif|png)$', re.IGNORECASE)
path_re = re.compile(r'/(images|uncategorized)/(\d{4}/\d{2}/\d{2}/[^/]+)$')
def substitute_ob_url(url):

    if url in funny_imgs:
        # Special case
        print_change(url, funny_imgs[url])
        return funny_imgs[url]

    (scheme, host, path, query, fragment) = urlparse.urlsplit(url)

    if host not in interesting_hosts:
        return url

    # Check if this is an image URL at OB
    match = ext_re.search(path) or ext_re.search(query)
    if match:
        match = path_re.search(match.group())
        if match:
            # Translate to new path
            host = 'lesswrong.com'
            path = '/static/imported/%s' % match.group(2)
            old_url = url
            url  = urlparse.urlunsplit((scheme, host, path, '', ''))
            print_change(old_url, url)
        else:
            print " Got unexpected image url: %s" % url

    return url

# Borrowed from the importer
url_re = re.compile(r"""(?:https?|ftp|file)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]""", re.IGNORECASE)
def process_content(html):
    if html:
        # if isinstance(text, str):
        #     text = text.decode('utf-8')
        #
        # # Double decode needed to handle some wierd characters
        # text = text.encode('utf-8')
        html = url_re.sub(lambda match: substitute_ob_url(match.group()), html)

    return html

# Main function
def fix_images(dryrun=True):
    from r2.models import Link, Comment

    links = Link._query(Link.c.ob_permalink != None, data = True)
    for link in links:
        ob_url = link.ob_permalink.strip()
        print "Processing %s" % ob_url

        new_content = process_content(link.article)
        if not dryrun:
            link.article = new_content
            link._commit()

        comments = Comment._query(Comment.c.link_id == link._id, data = True)
        for comment in comments:
            new_content = process_content(comment.body)
            if not dryrun:
                comment.body = new_content
                comment._commit()
