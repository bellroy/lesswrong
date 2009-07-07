from r2.lib.db.exporter import Exporter

def export_to(dbfile):
    e = Exporter(dbfile)
    e.export_db()
