from r2.tests import ModelTest
import nose
import mox
import pylons

class TestSelfLink(ModelTest):

    # def setup(self):
    #     self.subreddit_mock mox.Mox()

    def test_name(self):
        link = self.models.Link(name = 'Link Name')
        assert link.name == 'Link Name'

    def test_make_permalink(self):
        m  = mox.Mox()
        subreddit = m.CreateMock(self.models.Subreddit)
        #subreddit.name.AndReturn('stuff')
        m.ReplayAll()

        pylons.c.default_sr = True #False
        pylons.c.cname = False
        link = self.models.Link(name = 'Link Name', url = 'self', title = 'A link title', sr_id = 1)
        link._commit()
        permalink = link.make_permalink(subreddit)

        m.VerifyAll()
        assert permalink == '/lw/%s/a_link_title/' % link._id36


    # def test_make_permalink_slow(self):
    #
    #
    #     link = self.models.Link(name = 'Link Name', url = 'self', sr_id = 1)
    #     m = mox.Mox()
    #     mock_subreddit = mox.MockObject(self.models.Subreddit)
    #
    #     m.StubOutWithMock(link, 'subreddit_slow', use_mock_anything=True)
    #     link.subreddit_slow().AndReturn(mock_subreddit)
    #
    #     m.ReplayAll()
    #
    #     permalink = link.make_permalink_slow()
    #
    #     m.UnsetStubs()
    #     m.VerifyAll()


    def test_more_marker(self):
        test_cases = (
            ('asdf<a id="more"></a>lkjh', 'asdf', 'lkjh'),
        )
        for input_text, expected_summary, expected_more in test_cases:
            link = self.models.Link(article = input_text)
            link.article = input_text
            yield self.check_text, link._summary(), expected_summary
            yield self.check_text, link._more(), expected_more

    @staticmethod
    def check_text(output, expected_output):
        assert output == expected_output

