from r2.tests import ModelTest
import nose

class TestSelfLink(ModelTest):
    
    def setup(self):
        from r2.models import Link
        self.link = Link(name = 'Link Name', url = 'self')
    
    def teardown(self):
        # drop Link here
        self.link = None
    
    def test_name(self):
        print self.link
        assert self.link.name == 'Link Name'



