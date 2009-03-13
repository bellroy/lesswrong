from r2.tests import *

class TestLink(TestController):
    
    def setUp(self):
        response = self.app.get('/') # Hack that sets up the global environment
        # Create a link here
        from r2.models import Link  
        self.link = { 'name': 'Link Name' }
        pass
    
    def tearDown(self):
        # drop Link here
        self.link = None
        pass
    
    def test_name(self):
        print self.link
        assert self.link['name'] == 'Link Nane'

