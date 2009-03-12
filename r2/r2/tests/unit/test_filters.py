# -*- coding: utf-8 -*-
from r2.lib.filters import wrap_urls
import nose

def test_wrap_urls():
    test_cases = (
        ('http://www.plainlink.com', '<http://www.plainlink.com>'),
        ('before http://www.plainlink.com and http://www.plainlink2.com/asdf#here more',
            'before <http://www.plainlink.com> and <http://www.plainlink2.com/asdf#here> more'),
        ('(http://www.plainlink.com)', '(<http://www.plainlink.com>)'),
        ('Blah (http://www.plainlink.com)', 'Blah (<http://www.plainlink.com>)'),
        ('[Blah](http://www.plainlink.com)', '[Blah](http://www.plainlink.com)'),
        ('[Blah](http://www.plainlink.com/ÜnîCöde¡っ)', '[Blah](http://www.plainlink.com/ÜnîCöde¡っ)'),
        ('http://www.plainlink.com/ÜnîCöde¡', '<http://www.plainlink.com/ÜnîCöde¡>'),
        ('This is [an example](http://example.com/ "Title") inline link.',
            'This is [an example](http://example.com/ "Title") inline link.'),
        ('[This link](http://example.net/) has no title attribute.',
            '[This link](http://example.net/) has no title attribute.'),
        ('See my [About](/about/) page for details.', 'See my [About](/about/) page for details.'),
        ('This is [an example][id] reference-style link.', 'This is [an example][id] reference-style link.'),
        ('This is [an example] [id] reference-style link.\n\n[id]: http://example.com/  "Optional Title Here"',
            'This is [an example] [id] reference-style link.\n\n[id]: http://example.com/  "Optional Title Here"'),
        ("""[foo]: http://example.com/  "Optional Title Here"
            [foo]: http://example.com/  'Optional Title Here'
            [foo]: http://example.com/  (Optional Title Here)""",
         """[foo]: http://example.com/  "Optional Title Here"
            [foo]: http://example.com/  'Optional Title Here'
            [foo]: http://example.com/  (Optional Title Here)"""),
        ('[id]: <http://example.com/>  "Optional Title Here"',
            '[id]: <http://example.com/>  "Optional Title Here"'),
        ('[Google]: http://google.com/', '[Google]: http://google.com/'),
        ('[Daring Fireball]: http://daringfireball.net/', '[Daring Fireball]: http://daringfireball.net/'),
        ('Blah <http://a.link.com/> more', 'Blah <http://a.link.com/> more'),
    )
    for input_text, expected_output in test_cases:
        yield check_wrapped, wrap_urls(input_text), expected_output

def check_wrapped(output, expected_output):
    assert output == expected_output

if __name__ == '__main__':
    nose.main()