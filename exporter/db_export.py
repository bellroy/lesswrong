from r2.lib.db.exporter import Exporter

def export_to(dir):
    e = Exporter(dir)
    e.export_db()
