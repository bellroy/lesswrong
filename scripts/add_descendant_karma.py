from r2.models.link import Comment, Link

comments = list(Comment._query())
links = list(Link._query())

for comment in comments:
    comment._load()
    if hasattr(comment, 'parent_id'):
        Comment._byID(comment.parent_id).incr_descendant_karma(comment._ups - comment._downs)
    Link._byID(comment.link_id)._incr('_descendant_karma', (comment._ups - comment._downs))
