import yaml
from r2.models import Subreddit
from r2.lib.importer import Importer
import pylons

def import_posts(filename, sr_name):
    pylons.c.default_sr = True
    sr = Subreddit._by_name(sr_name)

    data = yaml.load(open(filename), Loader=yaml.CLoader)

    importer = Importer()
    importer.import_into_subreddit(sr, data)
