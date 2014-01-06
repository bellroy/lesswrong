from r2.lib.db.exporter import Exporter

# features is a sequence of features to extract.  Use db_export.sh to
# run each export in a separate python process and hopefully keep
# memory usage down.
def export_to(dbfile, features=None):
    e = Exporter(dbfile)
    if features is None:
        e.export_db()
    else:
        if 'users'     in features: e.export_users()
        if 'links'     in features: e.export_links()
        if 'comments'  in features: e.export_comments()
        if 'votes'     in features: e.export_votes()
        if 'indexes'   in features: e.create_indexes()
