import re
import sys

bare_link_re = re.compile(r'([^-A-Z0-9+&@#/%?=~_|!:,.;">]|^)(/lw/[^/]+/[^/]+/)([^-A-Z0-9+&@#/%?=~_|!:;"<]|$)')
linked_bare_link_re = re.compile(r'(<a href="[^"]+">)(/lw/[^/]+/[^/]+[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]</a>)')
spaces_around_anchor_re = re.compile(r'<a href\s+=\s+"([^"]+)"\s*>', re.IGNORECASE)
no_quotes_on_anchor_re = re.compile(r'<a href=([^>\'"]+)>([^<]+)</a>', re.IGNORECASE)
single_quotes_on_anchor_re = re.compile(r'<a href=\'([^>]+)\'>')
well_formed_uppercase_re = re.compile(r'<A [Hh][Rr][Ee][Ff]="([^"]+)">([^<]+)</A>')

def sub_group_1(match):
    return "<a href=\"%s\">" % match.group(1)

def sub_with_end_tag(match):
    return "<a href=\"%s\">%s</a>" % (match.group(1), match.group(2))

def wrap_bare_link(match):
    return '%s<a href="%s">http://lesswrong.com%s</a>%s' % (match.group(1), match.group(2), match.group(2), match.group(3))

def add_host_to_linked_bare_link(match):
    return match.group(1) + 'http://lesswrong.com' + match.group(2)

def rewrite_bare_links(content):
    # Tidy up strange HTML first
    content = spaces_around_anchor_re.sub(sub_group_1, content)
    content = no_quotes_on_anchor_re.sub(sub_with_end_tag, content)
    content = single_quotes_on_anchor_re.sub(sub_group_1, content)
    content = well_formed_uppercase_re.sub(sub_with_end_tag, content)
    
    # Fix bare links
    content = bare_link_re.sub(wrap_bare_link, content)
    content = linked_bare_link_re.sub(add_host_to_linked_bare_link, content)

    return content

def fix_bare_links(apply=False):
    from r2.models import Comment
    from r2.lib.db.thing import NotFound
    
    fbefore = open('fix_bare_links_before.txt', 'w')
    fafter  = open('fix_bare_links_after.txt', 'w')
    
    comment_id = 1
    try:
        # The comments are retrieved like this to prevent the API from 
        # attempting to load all comments at once and then iterating over them
        while True:
            comment = Comment._byID(comment_id, data=True)
        
            if (hasattr(comment, 'ob_imported') and comment.ob_imported) and (hasattr(comment, 'is_html') and comment.is_html):
                new_content = rewrite_bare_links(comment.body)
                
                if new_content != comment.body:
                    print >>fbefore, comment.body.encode('utf-8')
                    print >>fafter, new_content.encode('utf-8')
                    
                    if apply:
                        comment.body = new_content
                        comment._commit()
                    
                    try:
                        print >>sys.stderr, "Rewrote comment %s" % comment.make_permalink_slow().encode('utf-8')
                    except UnicodeError:
                        print >>sys.stderr, "Rewrote comment with id: %d" % comment._id
                    
            
            comment_id += 1
    except NotFound:
        # Assumes that comment ids are sequential and never deleted
        # (which I believe to true) -- wjm
        print >>sys.stderr, "Comment %d not found, exiting" % comment_id

    return
