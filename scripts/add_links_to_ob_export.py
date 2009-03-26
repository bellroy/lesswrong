import os
import sys
import yaml
import re

kill_whitespace_re = re.compile('\s')
kill_entities_re = re.compile('&#?[a-z0-9]{1,4};')
def kill_whitespace(body):
    body = kill_whitespace_re.sub('', body)
    body = kill_entities_re.sub('', body)
    body = body.replace('<p>', '')
    body = body.replace('</p>', '')
    body = body.replace('<br/>', '')
    
    return body

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
    mappings = yaml.load(api_file, Loader=yaml.CLoader)
    export   = yaml.load(export_file, Loader=yaml.CLoader)

    # Turn the mappings into a lookup table on title and content
    post_mapping = {}
    title_mapping = {}
    for post in mappings:
        title = post['title']
        body = post['description'] + post['mt_text_more']
        if not isinstance(body, unicode):
            body = unicode(body, 'utf-8')
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')

        key = (kill_whitespace(body), kill_whitespace(title))
        post_mapping[key] = post
        title_mapping[kill_whitespace(title)] = key

    # Scan the export file
    new_export = []
    for entry in export:
        if 'Eliezer Yudkowsky' not in entry['author']:
            continue

        # Get the title and do a lookup on the permalink
        body = entry['description'] + entry['mt_text_more']
        body = body.decode('utf-8')
        title = entry['title']
        title = title.decode('utf-8')
        print title
        # flush(sys.stdout)

        key = (kill_whitespace(body), kill_whitespace(title))
        try:
            api_post = post_mapping[key]
        except KeyError:
            print title_mapping[kill_whitespace(title)]
            print 
            print key
            print
            
            import difflib
            d = difflib.Differ()
            diff = d.compare(title_mapping[kill_whitespace(title)], key)
            import pprint
            pprint.pprint(list(diff))
            raise
        
        new_entry = entry
        new_entry['permalink'] = api_post['permaLink']
        new_entry['description'] = api_post['description']
        new_entry['mt_text_more'] = api_post['mt_text_more']
        new_entry['authorEmail'] = '\x73\x65\x6e\x74\x69\x65\x6e\x63\x65\x40\x70\x6f\x62\x6f\x78\x2e\x63\x6f\x6d'
        new_export.append(new_entry)
    
    # Print out the result
    yaml.dump(new_export, output_file, Dumper=yaml.CDumper)
        