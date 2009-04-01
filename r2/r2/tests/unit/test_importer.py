# -*- coding: utf-8 -*-
import nose

from r2.tests import ModelTest

from r2.lib.db.thing import NotFound

import r2.lib.importer
from r2.lib.importer import Importer

import re
import datetime
import pytz
import StringIO
import yaml

class ImporterFixture(object):

    def __init__(self):
        self.ids = {}
        self.data = []
        self.posts_by_id = {}

    def add_post(self,
                 author='Anonymous',
                 author_email='anon@nowhere.org',
                 category=['Category'],
                 title='Title',
                 description='',
                 mt_text_more='',
                 mt_keywords='',
                 status='Publish',
                 date_created=None,
                 permalink=None):
        post_id = self.post_id
        if not date_created:
            date_created = datetime.datetime.now().strftime('%m/%d/%Y %r')
        if not permalink:
            permalink = 'http://www.overcomingbias.com/%s.html' % post_id
        post = { 'postid': post_id,
                 'author': author,
                 'authorEmail': author_email,
                 'category': category,
                 'title': title,
                 'description': description,
                 'mt_text_more': mt_text_more,
                 'mt_keywords': mt_keywords,
                 'status': status,
                 'dateCreated': date_created,
                 'permalink': permalink }
        self.data.append(post)
        self.posts_by_id[post_id] = post
        return post_id

    def add_comment(self,
                    post_id,
                    author='Anonymous',
                    author_email='anon@nowhere.org',
                    author_url='',
                    body='',
                    date_created=None):
      if not date_created:
          date_created = datetime.datetime.now().strftime('%m/%d/%Y %r')

      comment = { 'author': author,
                  'authorEmail': author_email,
                  'authorUrl': author_url,
                  'body': body,
                  'dateCreated': date_created }

      self.posts_by_id[post_id].setdefault('comments', []).append(comment)

      return comment

    def __getattr__(self, attr):
        if attr.endswith('_id'):
            self.ids[attr] = self.ids.get(attr, 0) + 1
            return "%s-%d" % (attr[:-3], self.ids[attr])
        else:
            raise AttributeError, '%s not found' % attr

    def get_data(self):
        return self.data

class TestImporter(object):
    url_content = (
        ('Some text', 'Some text'),
        ('Blah <a href="http://www.overcomingbias.com/2007/11/passionately-wr.html">Link</a> more',
            'Blah <a href="http://www.overcomingbias-rewritten.com/2007/11/passionately-wr.html">Link</a> more'),
        ('Multiple urls: http://www.overcomingbias.com/ and http://overcomingbias.com and http://google.com/?q=test',
            'Multiple urls: http://www.overcomingbias-rewritten.com/ and http://overcomingbias-rewritten.com and http://google.com/?q=test'),
        ('Query string: http://www.google.com/search?rls=en-us&q=overcomingbias&ie=UTF-8&oe=UTF-8',
            'Query string: http://www.google.com/search?rls=en-us&q=overcomingbias-rewritten&ie=UTF-8&oe=UTF-8'),
        ('IP Address: http://72.14.235.104/?q=overcomingbias',
            'IP Address: http://72.14.235.104/?q=overcomingbias-rewritten'),
        ('Google cache: http://72.14.235.132/search?client=safari&rls=en-us&q=cache:http://www.overcomingbias.com/2007/11/passionately-wr.html&ie=UTF-8&oe=UTF-8',
            'Google cache: http://72.14.235.132/search?client=safari&rls=en-us&q=cache:http://www.overcomingbias-rewritten.com/2007/11/passionately-wr.html&ie=UTF-8&oe=UTF-8'),
        ("""Overcoming Bias links: http://www.overcomingbias.com
            http://www.overcomingbias.com/
            http://www.overcomingbias.com/2006/11/beware_heritabl.html
            http://www.overcomingbias.com/2006/11/beware_heritabl.html#comment-25685746""",
        """Overcoming Bias links: http://www.overcomingbias-rewritten.com
            http://www.overcomingbias-rewritten.com/
            http://www.overcomingbias-rewritten.com/2006/11/beware_heritabl.html
            http://www.overcomingbias-rewritten.com/2006/11/beware_heritabl.html#comment-25685746"""),
        ('Unicode: (http://www.overcomingbias.com/ÜnîCöde¡っ)', 'Unicode: (http://www.overcomingbias-rewritten.com/ÜnîCöde¡っ)'),
    )

    @staticmethod
    def url_rewriter(match):
        # This replacement will deliberately match again if the importer
        # processes the same url twice
        return match.group().replace('overcomingbias', 'overcomingbias-rewritten')

    @staticmethod
    def check_text(text, expected_text):
        assert text == expected_text

    def test_generate_password(self):
        pw_re = re.compile(r'[1-9a-hjkmnp-uwxzA-HJKMNP-UWXZ@#$%^&*]{8}')

        # This test is a bit questionable given the random generation
        # but its better than no test
        for i in range(10):
            password = r2.lib.importer.generate_password()
            # print password
            assert pw_re.match(password)

    def test_filter_html_in_titles(self):
        pass

    def test_set_comment_is_html(self):
        pass

    def test_auto_account_creation(self):
        pass

    def test_cleaning_of_content(self):
        # There are a lot of ^M's in the comments
        pass

from mocktest import *
from r2.models import Account, Link, Comment
from r2.models.account import AccountExists
class TestImporterMocktest(TestCase):

    @property
    def importer(self):
        return Importer()

    @property
    def post(self):
        post_anchor = mock_on(Link)
        post = mock_wrapper().named('post')
        post_anchor._submit.returning(post.mock)
        return post

    def test_get_or_create_account_prev_imported_exists(self):
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper().named('subreddit')

        account = mock_wrapper().named('account')

        account_anchor = mock_on(Account)
        account_anchor.c.with_children(ob_account_name='Test User', email='user@host.com')
        query = account_anchor._query.returning([account.mock])

        mock_on(r2.lib.importer).register.is_expected.no_times()

        post = self.post

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        args = query.called.once().get_args()
        assert args == ((True, True), {'data': True})

    def test_get_or_create_account_exists(self):
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper()
        account_anchor._query.returning([account.mock]).is_expected

        mock_on(r2.lib.importer).register.is_expected.no_times()

        post = self.post

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_exists2(self):
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        def query_action(name_match, email_match, data):
            return [account.mock] if name_match and email_match else []

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper()
        query = account_anchor._query
        query.action = query_action
        query.is_expected.thrice() # Third attempt should succeed
        account_anchor.c.with_children(ob_account_name='bogus', name='TestUser', email='user@host.com')

        mock_on(r2.lib.importer).register.is_expected.no_times()

        post = self.post

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_exists3(self):
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        def query_action(name_match, email_match, data):
            return [account.mock] if name_match and email_match else []

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper()
        query = account_anchor._query
        query.action = query_action
        query.is_expected.exactly(4).times # Fourth attempt should succeed
        account_anchor.c.with_children(ob_account_name='bogus', name='Test_User', email='user@host.com')

        mock_on(r2.lib.importer).register.is_expected.no_times()

        post = self.post

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_not_exists(self):
        """Should create the account if it doesn't exist"""
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query
        query.return_value = []
        query.is_expected.exactly(4).times

        test_user = mock_wrapper().named('Test_User').with_methods(_safe_load=None, _commit=None).unfrozen()
        test_user.with_children(ob_account_name='bogus')

        def register_action(name, password, email):
            if name != test_user.name:
                raise AccountExists
            else:
                return test_user.mock

        def check_register_args(name, password, email):
            return name == test_user.name and email == 'user@host.com'

        # Mocking on importer because it imported register
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register
        register.action = register_action
        register.is_expected.where_args(check_register_args)

        post = self.post

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        assert test_user.mock.ob_account_name == 'Test User'

    def test_create_account_multiple_attempts(self):
        """Make multiple attempts to create a new account"""
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query
        query.return_value = []
        query.is_expected.exactly(4).times

        test_user5 = mock_wrapper().named('Test_User5').with_methods(_safe_load=None, _commit=None).unfrozen()
        test_user5.with_children(ob_account_name='bogus')

        def register_action(name, password, email):
            if name != test_user5.name:
                raise AccountExists
            else:
                return test_user5.mock

        # Mocking on importer because it imported register
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register
        register.is_expected.exactly(5).times
        register.action = register_action

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        post = self.post

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        assert test_user5.mock.ob_account_name == 'Test User'

    def test_get_or_create_account_max_retries(self):
        """Should raise an error after 100 tries"""
        fixture = ImporterFixture()
        post_id = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query.returning([]).is_expected.exactly(4).times
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register.raising(AccountExists).is_expected.exactly(100).times

        post = self.post

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_cached(self):
        """Test name to account lookup is cached"""
        fixture = ImporterFixture()
        fixture.add_post(author='Test User', author_email='user@host.com', description='Post 1')
        fixture.add_post(author='Test User', author_email='user@host.com', description='Post 2')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query
        query.return_value = []
        query.is_expected.exactly(4).times

        test_user5 = mock_wrapper().named('Test_User5').with_methods(_safe_load=None, _commit=None).unfrozen()
        test_user5.with_children(ob_account_name='bogus')

        def register_action(name, password, email):
            if name != test_user5.name:
                raise AccountExists
            else:
                return test_user5.mock

        # Mocking on importer because it imported register
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register
        register.is_expected.exactly(5).times
        register.action = register_action

        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([])

        post = self.post

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        assert test_user5.mock.ob_account_name == 'Test User'

    def test_create_post(self):
        author = 'Test User'
        author_email = 'user@host.com'
        category = ['Self-Deception', 'Prediction Markets']
        expected_category = ['self_deception', 'prediction_markets']
        title = 'Test Title with some special <i>italic text</i> and <u>underline text</u> and <b>bold text</b>.'
        expected_title = 'Test Title with some special italic text and underline text and bold text.'
        description = 'A short test description'
        ip = '127.0.0.1'
        local_date_created = pytz.timezone('America/New_York').localize(datetime.datetime(2009, 11, 1, 1, 0, 0), is_dst=False)
        utc_date_created = local_date_created.astimezone(pytz.utc)
        permalink = 'http://www.overcomingbias.com/2009/03/test.html'

        fixture = ImporterFixture()
        post_id = fixture.add_post(author=author,
                                   author_email=author_email,
                                   category=category,
                                   title=title,
                                   description=description,
                                   date_created=local_date_created.strftime('%m/%d/%Y %I:%M:%S %p'),
                                   permalink=permalink)

        sr = mock_wrapper().named('subreddit')

        account_anchor = mock_on(Account)
        account = mock_wrapper().named('account')
        account_anchor._query.returning([account.mock])

        post = mock_wrapper().named('post')
        post.expects('_commit')
        post.with_children(_id='post id', blessed=False, comment_sort_order='new', ob_permalink='bogus')
        post_anchor = mock_on(Link)
        post_anchor._query.returning([]).is_expected
        submit = post_anchor._submit.returning(post.mock)

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        self.assertEqual(submit.called.once().get_args(),
                         ((expected_title, description, account.mock, sr.mock, ip, expected_category), {'date': utc_date_created}))
        self.assertTrue(post.mock.blessed, 'The post should be promoted')
        self.assertEqual(post.mock.comment_sort_order, 'old')
        self.assertEqual(post.mock.ob_permalink, permalink)

    def test_create_post_with_more(self):
        author = 'Test User'
        author_email = 'user@host.com'
        category = ['Prediction Markets']
        expected_category = ['prediction_markets']
        title = 'Test Title'
        description = 'A short test description'
        mt_text_more = u'This is more text \u2019 after the fold.'
        ip = '127.0.0.1'
        article = description + Link._more_marker + mt_text_more
        local_date_created = pytz.timezone('America/New_York').localize(datetime.datetime(2009, 11, 1, 1, 0, 0), is_dst=False)
        utc_date_created = local_date_created.astimezone(pytz.utc)
        permalink = 'http://www.overcomingbias.com/2009/03/test.html'
        comment_author = 'Comment Author'
        comment_author_email = 'comment_author@nowhere.org'
        comment_body = 'A short test comment'
        local_comment_date_created = pytz.timezone('America/New_York').localize(datetime.datetime(2009, 11, 1, 1, 0, 0), is_dst=False)
        utc_comment_date_created = local_comment_date_created.astimezone(pytz.utc)

        fixture = ImporterFixture()
        post_id = fixture.add_post(author=author,
                                   author_email=author_email,
                                   category=category,
                                   title=title,
                                   description=description,
                                   mt_text_more=mt_text_more,
                                   date_created=local_date_created.strftime('%m/%d/%Y %I:%M:%S %p'),
                                   permalink=permalink)
        fixture.add_comment(post_id=post_id,
                            author=comment_author,
                            author_email=comment_author_email,
                            body=comment_body,
                            date_created=local_comment_date_created.strftime('%m/%d/%Y %I:%M:%S %p'))

        sr = mock_wrapper().named('subreddit')

        account_for_post = mock_wrapper().named('account for post').with_methods(_safe_load=None, _commit=None)
        account_for_comment = mock_wrapper().named('account for comment').with_methods(_safe_load=None, _commit=None)
        account_generator = ([account.mock] for account in (account_for_post, account_for_comment))
        account_anchor = mock_on(Account)
        account_anchor._query.named('Account._query').with_action(lambda *args, **kwargs: account_generator.next())

        post = mock_wrapper().named('post')
        post.with_children(_id='post id', blessed=False, comment_sort_order='new', ob_permalink='bogus').unfrozen()
        post.expects('_commit')
        post_anchor = mock_on(Link)
        post_anchor._query.returning([])
        submit = post_anchor._submit.named('Link._submit').returning(post.mock)

        comment = mock_wrapper().named('comment')
        comment.expects('_commit')
        comment.with_children(is_html=False, ob_imported=False)
        inbox_rel = None
        comment_anchor = mock_on(Comment)
        new = comment_anchor._new.named('Comment._new').returning((comment.mock, inbox_rel))

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        self.assertEqual(submit.called.once().get_args(),
                         ((title, article, account_for_post.mock, sr.mock, ip, expected_category), {'date': utc_date_created}))
        self.assertTrue(post.mock.blessed, 'The post should be promoted')
        self.assertEqual(post.mock.comment_sort_order, 'old')
        self.assertEqual(post.mock.ob_permalink, permalink)

        self.assertEqual(new.called.once().get_args(),
                         ((account_for_comment.mock, post.mock, None, comment_body, ip), {'date': utc_comment_date_created}))
        self.assertTrue(comment.mock.is_html, 'The comment should be marked as HTML')
        self.assertTrue(comment.mock.ob_imported, 'The comment should be marked as imported from OB')

    def test_create_post_prev_imported_exists(self):
        author = 'Test User'
        author_email = 'user@host.com'
        category = ['Self-Deception', 'Prediction Markets']
        expected_category = ['self_deception', 'prediction_markets']
        title = 'Test Title with some special <i>italic text</i> and <u>underline text</u> and <b>bold text</b>.'
        expected_title = 'Test Title with some special italic text and underline text and bold text.'
        description = 'A short test description'
        ip = '127.0.0.1'
        local_date_created = pytz.timezone('America/New_York').localize(datetime.datetime(2009, 11, 1, 1, 0, 0), is_dst=False)
        utc_date_created = local_date_created.astimezone(pytz.utc)
        permalink = 'http://www.overcomingbias.com/2009/03/test.html'
        comment_author = 'Comment Author'
        comment_author_email = 'comment_author@nowhere.org'
        comment_body = 'A short test comment'
        local_comment_date_created = pytz.timezone('America/New_York').localize(datetime.datetime(2009, 11, 1, 1, 0, 0), is_dst=False)
        utc_comment_date_created = local_comment_date_created.astimezone(pytz.utc)

        fixture = ImporterFixture()
        post_id = fixture.add_post(author=author,
                                   author_email=author_email,
                                   category=category,
                                   title=title,
                                   description=description,
                                   date_created=local_date_created.strftime('%m/%d/%Y %I:%M:%S %p'),
                                   permalink=permalink)
        fixture.add_comment(post_id=post_id,
                            author=comment_author,
                            author_email=comment_author_email,
                            body=comment_body,
                            date_created=local_comment_date_created.strftime('%m/%d/%Y %I:%M:%S %p'))

        sr = mock_wrapper().named('subreddit').with_children(_id='subreddit id')

        account_for_post = mock_wrapper().named('account for post').with_children(_id='account for post id')
        account_for_comment = mock_wrapper().named('account for comment').with_children(_id='account for comment id')
        account_generator = ([account.mock] for account in (account_for_post, account_for_comment))
        account_anchor = mock_on(Account)
        account_anchor._query.named('Account._query').with_action(lambda *args, **kwargs: account_generator.next())

        post = mock_wrapper().named('post')
        post.with_children(_id='post id', title=None, article=None, author_id=None, sr_id=None, ip=None, date=None).unfrozen()
        post.with_methods(set_tags=None).unfrozen()
        post.expects('_commit')
        post.expects('set_tags')
        post_anchor = mock_on(Link)
        post_anchor._query.returning([post.mock])

        comment = mock_wrapper().named('comment')
        comment.with_children(author_id=None, body=None, ip=None, date=None, is_html=False, ob_imported=False).unfrozen()
        comment.expects('_commit')
        comment_anchor = mock_on(Comment)
        comment_anchor._query.named('Comment._query').returning([comment.mock])

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

        self.assertEqual(post.mock.title, expected_title)
        self.assertEqual(post.mock.article, description)
        self.assertEqual(post.mock.author_id, account_for_post.mock._id)
        self.assertEqual(post.mock.sr_id, sr.mock._id)
        self.assertEqual(post.mock.ip, ip)
        self.assertEqual(post.mock._date, utc_date_created)

        self.assertEqual(comment.mock.author_id, account_for_comment.mock._id)
        self.assertEqual(comment.mock.body, comment_body)
        self.assertEqual(comment.mock.ip, ip)
        self.assertEqual(comment.mock._date, utc_comment_date_created)
        self.assertTrue(comment.mock.is_html)
        self.assertTrue(comment.mock.ob_imported)

    @ignore
    def test_failing_post(self):
        self.assertRaises(
            StandardError, lambda: self.importer._get_or_create_account('Test User', 'user@host.com'),
            message='Unable to generate account after 10 retries')

    @ignore
    def test_import_into_subreddit(self):
        sr = mock_wrapper()

        fixture = ImporterFixture()
        post_id = fixture.add_post()
        fixture.add_comment(post_id=post)

        importer = Importer()
        importer.import_into_subreddit(sr, fixture.get_data())

    @ignore
    def test_set_sort_order(self):
        fixture = ImporterFixture()
        post_id = fixture.add_post()
        fixture.add_comment(post)
        importer = Importer()
        sr = mock_wrapper()
        link = mock_wrapper()
        mock_link = mock_on(Link)
        mock_link.create.returning(link.mock).with_args().is_expected
        importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_rewrite_ob_urls(self):
        post_no_urls = mock_wrapper().named('post with no urls').with_children(
            _id=1,
            article='This is the post body',
            url='http://lesswrong.com/lw/2d/missing-alliances/',
            ob_permalink='http://www.overcomingbias.com/2009/03/missing-alliances.html').unfrozen()
        post_no_urls.expects('_commit')
        post_no_urls.frozen()

        post_no_ob_urls = mock_wrapper().named('post with no ob urls').with_children(
            _id=2,
            article='Google: http://google.com/',
            url='new2',
            ob_permalink='old2').unfrozen()
        post_no_ob_urls.expects('_commit')
        post_no_ob_urls.frozen()

        post_ob_urls = mock_wrapper().named('post with ob urls').with_children(
            _id=3,
            article=u'Blah\nblerg http://www.overcomingbias.com/2009/03/missing-alliances.html blah',
            url='new3',
            ob_permalink='old3').unfrozen()
        post_ob_urls.expects('_commit')
        post_ob_urls.frozen()

        posts = [post_no_urls, post_no_ob_urls, post_ob_urls]

        post_anchor = mock_on(Link)
        post_anchor.c.with_children(ob_permalink='not None')
        post_query = post_anchor._query.returning([post.mock for post in posts])

        comment_no_urls = mock_wrapper().named('comment with no urls').with_children(body='Comment *body*, no links.')
        comment_no_urls.unfrozen().expects('_commit')
        comment_no_urls.frozen()
        
        comment_no_ob_urls = mock_wrapper().named('comment with no ob urls').with_children(body='Google:\nhttp://google.com/ is good')
        comment_no_ob_urls.unfrozen().expects('_commit')
        comment_no_ob_urls.frozen()
        
        comment_ob_urls = mock_wrapper().named('comment with ob urls').with_children(body='Blah http://www.overcomingbias.com/2009/03/missing-alliances.html blah')
        comment_ob_urls.unfrozen().expects('_commit')
        comment_ob_urls.frozen()

        comment_generator = ([comment.mock] for comment in (comment_no_urls, comment_no_ob_urls, comment_ob_urls))
        comment_anchor = mock_on(Comment)
        comment_query = comment_anchor._query.with_action(lambda *args, **kwargs: comment_generator.next())

        sr = mock_wrapper().named('subreddit')

        self.importer.import_into_subreddit(sr, [])

        args = post_query.called.once().get_args()
        assert args == ((True,), {'data': True})

        self.assertEqual(post_no_urls.mock.article, 'This is the post body')
        self.assertEqual(post_no_ob_urls.mock.article, 'Google: http://google.com/')
        self.assertEqual(post_ob_urls.mock.article, 'Blah\nblerg http://lesswrong.com/lw/2d/missing-alliances/ blah')

        comment_query.called.thrice()

        self.assertEqual(comment_no_urls.mock.body, 'Comment *body*, no links.')
        self.assertEqual(comment_no_ob_urls.mock.body, 'Google:\nhttp://google.com/ is good')
        self.assertEqual(comment_ob_urls.mock.body, 'Blah http://lesswrong.com/lw/2d/missing-alliances/ blah')

    def test_generate_mapping_file(self):
        post_no_urls = mock_wrapper().named('post with no urls').with_children(
            _id=1,
            article='This is the post body',
            url='http://lesswrong.com/lw/2d/missing-alliances/',
            ob_permalink='http://www.overcomingbias.com/2009/03/missing-alliances.html').unfrozen()
        post_no_urls.with_methods(_commit=None)

        post_no_ob_urls = mock_wrapper().named('post with no ob urls').with_children(
            _id=2,
            article='Google: http://google.com/',
            url='new2',
            ob_permalink='old2').unfrozen()
        post_no_ob_urls.with_methods(_commit=None)

        post_ob_urls = mock_wrapper().named('post with ob urls').with_children(
            _id=3,
            article='Blah\nblerg http://www.overcomingbias.com/2009/03/missing-alliances.html blah',
            url='new3',
            ob_permalink='old3').unfrozen()
        post_ob_urls.with_methods(_commit=None)

        post_anchor = mock_on(Link)
        post_anchor.c.with_children(ob_permalink='not None')
        post_query = post_anchor._query.returning([post.mock for post in [post_no_urls, post_no_ob_urls, post_ob_urls]])

        comment_anchor = mock_on(Comment)
        comment_query = comment_anchor._query.returning([])

        sr = mock_wrapper().named('subreddit')

        builtin_anchor = mock_on(r2.lib.importer)
        import_mapping_file = StringIO.StringIO()
        builtin_anchor.open.with_args('import_mapping.yml', 'w').returning(import_mapping_file).is_expected

        post_mapping = {
            'http://www.overcomingbias.com/2009/03/missing-alliances.html': 'http://lesswrong.com/lw/2d/missing-alliances/',
            'old2': 'new2',
            'old3': 'new3',
        }
        yaml_anchor = mock_on(yaml)
        dump = yaml_anchor.dump

        self.importer.import_into_subreddit(sr, [])

        args = dump.called.once().get_args()
        assert args == ((post_mapping, import_mapping_file), {'Dumper': yaml.CDumper})
