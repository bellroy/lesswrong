# -*- coding: utf-8 -*-
from fix_link_urls import convert_url, should_convert_url
import unittest

class TestFixLinksUrls(unittest.TestCase):
    inputs = (
        (u'/r/wmoore-drafts/comments/1/continue_editing/', True, '/lw/1/continue_editing/'),
        (u'/a/1l/image_post/', True, '/lw/1l/image_post/'),
        (u'/r/currentaffairs/comments/s/hi_im_new_here/', True, u'/lw/s/hi_im_new_here/'),
        (u'/r/New-User-drafts/comments/t/draft_post/', True, u'/lw/t/draft_post/'),
        (u'/r/selfdeception/comments/p/mixed_case_tags/', True, u'/lw/p/mixed_case_tags/'),
        (u'/r/hypocrisy/comments/16/unknown_tag/', True, u'/lw/16/unknown_tag/'),
        (u'/r/politics/comments/17/an_african_folktale/', True, u'/lw/17/an_african_folktale/'),
        (u'/r/future/comments/1a/ウ/', True, u'/lw/1a/ウ/'),
        (u'/r/New-User-drafts/comments/1b/embeded_flash_player/', True, u'/lw/1b/embeded_flash_player/'),
        (u'/comments/1c/where_do_i_go/', True, u'/lw/1c/where_do_i_go/'),
        (u'/r/wmoore-drafts/comments/h/a_new_article/', True, u'/lw/h/a_new_article/'),
        (u'self', False, u'/lw/self/'),
        (u'/r/meta/comments/1h/about_lesswrong/', True, u'/lw/1h/about_lesswrong/'),
        (u'/r/ads/lw/1t/submit_to_ads/', True, u'/lw/1t/submit_to_ads/'),
        (u'/r/admin/comments/1i/about_lesswrong/', True, u'/lw/1i/about_lesswrong/'),
        (u'/article/1j/htmlinptitlep/', True, u'/lw/1j/htmlinptitlep/'),
        (u'/a/1k/phtmlp/', True, u'/lw/1k/phtmlp/'),
        (u'/comments/x/just_be_glad_its_not_2girls1cup/', True, u'/lw/x/just_be_glad_its_not_2girls1cup/'),
        (u'/lw/1k/arrgos_ijgl_sldfjg_dsfg/', False, u'/lw/1k/arrgos_ijgl_sldfjg_dsfg/'),
        (u'/lw/15/another_relative_url_test/', False, u'/lw/15/another_relative_url_test/'),
        (u'/lw/y/removed_html_in_title_2/', False, u'/lw/y/removed_html_in_title_2/'),
        (u'/article/y/removed_html_in_title_2/', True, u'/lw/y/removed_html_in_title_2/'),
    )
        
    def test_pattern_match(self):
        for url, should_convert, converted_url in self.inputs:
            self.assertEqual(should_convert_url(url), should_convert )
        
    def test_conversion(self):
        for url, should_convert, converted_url in self.inputs:
            self.assertEqual(convert_url(url), converted_url)
            
            
            
if __name__ == '__main__':
    unittest.main()