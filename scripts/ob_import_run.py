import yaml
from r2.models import Subreddit
from r2.lib.importer import Importer
import pylons

def import_posts(input_filename, rewrite_filename, sr_name):
    pylons.c.default_sr = True
    sr = Subreddit._by_name(sr_name)

    input_file = open(input_filename)
    rewrite_file = open(rewrite_filename, 'w')

    data = yaml.load(input_file, Loader=yaml.CLoader)

    importer = Importer()
    importer.import_into_subreddit(sr, data, rewrite_file)
