# -*- coding: utf-8 -*-
from r2.lib.filters import wrap_urls, killhtml, format_linebreaks
import nose

def is_equal(output, expected_output):
    assert output == expected_output

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
        yield is_equal, wrap_urls(input_text), expected_output

def test_killhtml():
    """Test killhtml removes all tags"""
    test_cases = (
        ('Just Text', 'Just Text'),
        ('<p>One</p><p>Two</p>', 'One Two'),
        ('<p>One</p>     \n  <p>Two</p>', 'One Two'),
        ('<p>One</p>\n<p>Two</p>', 'One Two'),
        ('Some Text<p>then tag</p>', 'Some Text then tag'),
        ('<p>Some Text</p>then no tag.', 'Some Text then no tag.'),
        ('Entities &amp; &lt;hr/&gt;', 'Entities & <hr/>'),
        ('<p>Unknown tags: <asdf>qwerty</asdf>', 'Unknown tags: qwerty'),
    )
    for input_text, expected_output in test_cases:
        yield is_equal, killhtml(input_text), expected_output

def test_format_linebreaks():
    """Test replacing of line breaks with br tags"""
    test_cases = (
        ('Simple:\n\nLine two', '<p>Simple:</p><p>Line two</p>'),
        ('DOS:\r\n\r\nLine breaks', '<p>DOS:</p><p>Line breaks</p>'),
        ('Classic Mac:\r\rLine breaks', '<p>Classic Mac:</p><p>Line breaks</p>'),
        ('Consecutive:\n\n\n\n\n\nLine breaks', '<p>Consecutive:</p><p>Line breaks</p>'),
        ('Multiple:\r\n\r\nLine\r\n\r\nbreaks', '<p>Multiple:</p><p>Line</p><p>breaks</p>'),
        ('\nLeading and trailing\n', '<p>Leading and trailing</p>'),
        ('Single\ndoesn\'t wrap', '<p>Single\ndoesn\'t wrap</p>'),
    )
    for input_text, expected_output in test_cases:
        yield is_equal, format_linebreaks(input_text), expected_output

if __name__ == '__main__':
    nose.main()