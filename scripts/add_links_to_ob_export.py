import os
import sys
import yaml
import re

kill_whitespace_re = re.compile('\s')
def kill_whitespace(body):
    return kill_whitespace_re.sub('', body)

if __name__ == '__main__':
    if len(sys.argv) <= 3:
        print 'Usage: %s <export_file> <api_file> <outputfile>' % os.path.basename(sys.argv[0])
        print
        print ' Uses the api_file to supplement the export_file with permalinks.'
        print ' Writes the result to outputfile.'
        sys.exit(-1)

    export_file = open(sys.argv[1])
    api_file = open(sys.argv[2])
    output_file = open(sys.argv[3], 'w')
    mappings = yaml.load(api_file)
    export   = yaml.load(export_file)

    # Turn the mappings into a lookup table on title and content
    post_mapping = {}
    title_mapping = {}
    for post in mappings:
        print post['title']
        
        title = post['title']
        body = post['description'] + post['mt_text_more']
        if not isinstance(body, unicode):
            body = unicode(body, 'utf-8')
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')

        key = (kill_whitespace(body), kill_whitespace(title))
        post_mapping[key] = post
        title_mapping[title] = key

    # Scan the export file
    for entry in export:
        # Get the date and title and do a lookup on the permalink
        body = entry['description'] + entry['mt_text_more']
        body = body.decode('utf-8')
        title = entry['title']
        title = title.decode('utf-8')

        key = (kill_whitespace(body), kill_whitespace(title))
        try:
            api_post = post_mapping[key]
        except KeyError:
            print title_mapping[entry['title']]
            print 
            print key
            print
            raise
            
        entry['permalink'] = api_post['permaLink']
        entry['description'] = api_post['description']
        entry['mt_text_more'] = api_post['mt_text_more']
    
    # Print out the result
    yaml.dump(export, output_file)
        