# -*- coding: utf-8 -*-
from fix_bare_links import rewrite_bare_links

import yaml
import os.path
import unittest

class TestFixImportedImages(unittest.TestCase):
        
    def test_correction(self):
        test_cases = yaml.load(open(os.path.normpath(os.path.join(__file__, '..', "fix_bare_links_test_cases.yml"))), Loader=yaml.CLoader)
        for source, expected_output in test_cases:
            try:
                self.assertEqual(rewrite_bare_links(source), expected_output)
            except TypeError:
                import pprint
                pprint.pprint(source)
                pprint.pprint(expected_output)
                raise
            
if __name__ == '__main__':
    unittest.main()
