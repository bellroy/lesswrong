import re

def convert_url(url):
    parts = filter(None, url.split('/'))
    return "/lw/%s/" % '/'.join(parts[-2:])

good_url_regex = re.compile('^/lw/.*|self')
def should_convert_url(url):
    return not good_url_regex.match(url)

def get_links():
    from r2.models import Link
    q = Link._query(data=True)
    return list(q)

def fix_link_urls(links, force=False):
    for link in links:
        if force or should_convert_url(link.url):
            new_url = convert_url(link.url)
            print "%s => %s" % (link.url, new_url)
            link.url = new_url
            link._commit()
            link.set_url_cache()

def print_link_urls(links, force=False):
    print "Link URLs to fix:"
    for link in links:
        if force or should_convert_url(link.url):
            new_url = convert_url(link.url)
            print "%s => %s" % (link.url, new_url)

def staging_links():
    from r2.models import Link
    ids = (
        int('1', 36),
        int('4', 36),
        int('5', 36),
        int('6', 36),
        int('8', 36),
        int('9', 36),
        int('a', 36),
        int('3', 36),
        int('7', 36),
        int('b', 36),
        int('c', 36),
        int('d', 36),
        int('e', 36),
        int('f', 36),
        int('k', 36),
        int('l', 36),
        int('j', 36),
        int('p', 36),
        int('q', 36),
        int('r', 36),
        int('t', 36),
        int('u', 36),
        int('y', 36),
        int('11', 36),
        int('12', 36),
        int('z', 36),
        int('2', 36),
        int('13', 36),
        int('o', 36),
        int('n', 36),
        int('10', 36),
        int('i', 36),
        int('h', 36),
        int('g', 36),
    )
    return Link._byID(ids, data=True, return_dict=False)
