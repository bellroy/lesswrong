# -*- coding: utf-8 -*-
from fix_imported_content_with_images import process_content
import unittest

class TestFixImportedImages(unittest.TestCase):
    sample_content = (
        ('asdf http://robinhanson.typepad.com/.a/6a00d8341c6a2c53ef010536c21d63970b-800wi asdf', 'asdf http://lesswrong.com/static/imported/6a00d8341c6a2c53ef010536c21d63970b-800wi.jpg asdf'),
        ('http://robinhanson.typepad.com/photos/uncategorized/2007/09/19/lindacorrelation.png', 'http://lesswrong.com/static/imported/2007/09/19/lindacorrelation.png'),
        ('http://robinhanson.typepad.com/photos/uncategorized/2008/05/06/bayestheorem.png', 'http://lesswrong.com/static/imported/2008/05/06/bayestheorem.png'),
        ('http://www.overcomingbias.com/images/2007/08/10/monsterwithgirl_2.jpg', 'http://lesswrong.com/static/imported/2007/08/10/monsterwithgirl_2.jpg'),
        ('http://www.overcomingbias.com/images/2008/09/30/zebra_4.jpg', 'http://lesswrong.com/static/imported/2008/09/30/zebra_4.jpg'),
        ('<a href="http://www.overcomingbias.com/images/2008/05/27/jbarbourrelative.png"><img src="http://www.overcomingbias.com/images/2008/05/27/jbarbourrelative.png" /></a>', '<a href="http://lesswrong.com/static/imported/2008/05/27/jbarbourrelative.png"><img src="http://lesswrong.com/static/imported/2008/05/27/jbarbourrelative.png" /></a>'),
        ("Not OB http://www.notovercomingbias.com/images/2008/05/27/jbarbourrelative.png", "Not OB http://www.notovercomingbias.com/images/2008/05/27/jbarbourrelative.png"),
        (u'••• http://www.overcomingbias.com/images/2007/08/10/monsterwithgirl_2.jpg', u'••• http://lesswrong.com/static/imported/2007/08/10/monsterwithgirl_2.jpg'),
        ('http://robinhanson.typepad.com/.shared/image.html?/photos/uncategorized/2008/05/22/mindscaleparochial.png',       'http://lesswrong.com/static/imported/2008/05/22/mindscaleparochial.png'),
        ('http://robinhanson.typepad.com/photos/uncategorized/2008/05/26/schrodinger.gif', 'http://lesswrong.com/static/imported/2008/05/26/schrodinger.gif')
    )
        
    def test_correction(self):
        for source, expected_output in self.sample_content:
            self.assertEqual(process_content(source), expected_output)
            
if __name__ == '__main__':
    unittest.main()
