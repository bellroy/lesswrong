from r2.models.link import Comment

comments = list(Comment._query())

for comment in comments:
    if hasattr(comment, 'parent_id'):
        Comment._byID(comment.parent_id).incr_descendant_karma(comment._ups - comment._downs)
