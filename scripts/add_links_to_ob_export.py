from gdata import atom
import sys
import yaml
import datetime

ZERO = datetime.timedelta(0)
KIND_SCHEME = 'http://schemas.google.com/g/2005#kind'


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
        

if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print 'Usage: %s <export_file> <api_file>' % os.path.basename(sys.argv[0])
        print
        print ' Uses the api_file to supplement the export_file with permalinks.'
        sys.exit(-1)

    export_file = open(sys.argv[1])
    api_file = open(sys.argv[2])
    mappings = yaml.load(api_file)
    export   = yaml.load(export_file)

    # Turn the mappings into a lookup table on title and content
    post_mapping = {}
    title_mapping = {}
    for post in mappings:
        print post['title']
        # 2006-11-20 11:00:00
        date = post['dateCreated']
        body = post['description'].strip() + post['mt_text_more'].strip()
        post_mapping[(body, post['title'])] = post['permaLink']
        title_mapping[post['title']] = body

    # Scan the export file
    for entry in export:
        # Get the date and title and do a lookup on the permalink
        body = post['description'].strip() + post['mt_text_more'].strip()
        try:
            permalink = post_mapping[(body, entry['title'])]
        except KeyError:
            print title_mapping[entry['title']]
            print 
            print body
            print
            raise
            
        print permalink
        