import re
import yaml
import pytz
import urlparse
import datetime
from random import Random
from BeautifulSoup import BeautifulSoup

from r2.models import Link,Comment,Account,Subreddit,FakeAccount
from r2.models.account import AccountExists, register
from r2.lib.db.thing import NotFound

DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
INPUT_TIMEZONE = pytz.timezone('America/New_York')
MAX_RETRIES = 100

dryrun = True
username_mapping = {}

# Constants for the characters to compose a password from.
# Easilty confused characters like I and l, 0 and O are omitted
PASSWORD_NUMBERS='123456789'
PASSWORD_LOWER_CHARS='abcdefghjkmnpqrstuwxz'
PASSWORD_UPPER_CHARS='ABCDEFGHJKMNPQRSTUWXZ'
PASSWORD_OTHER_CHARS='@#$%^&*'
ALL_PASSWORD_CHARS = ''.join([PASSWORD_NUMBERS,PASSWORD_LOWER_CHARS,PASSWORD_UPPER_CHARS,PASSWORD_OTHER_CHARS])

rng = Random()
def generate_password():
    password = []
    for i in range(8):
        password.append(rng.choice(ALL_PASSWORD_CHARS))
    return ''.join(password)

def comment_excerpt(comment):
  excerpt = comment['body'].replace("\n", '')[0:50]
  return "comment by '%s': %s" % (comment['author'], excerpt)

re_non_alphanum = re.compile(r'[^a-zA-Z0-9]*')
def comment_exists(post, comment):
    # Check if this comment already exists using brutal compare on content
    # BeautifulSoup is used to parse as HTML in order to remove markup
    content = ''.join(BeautifulSoup(comment['body']).findAll(text=True))
    key = re_non_alphanum.sub('', content)
    existing_comments = Comment._query(Comment.c.link_id == post._id, Comment.c.ob_imported == True, data=True)
    for existing_comment in existing_comments:
        author = Account._byID(existing_comment.author_id, data=True)
        content = ''.join(BeautifulSoup(existing_comment.body).findAll(text=True))
        existing_key = re_non_alphanum.sub('', content)
        if key == existing_key:
            print " Skipping existing %s" % comment_excerpt(comment)
            return True
        # else:
        #     print "%s *|NOT|* %s" % (key, existing_key)

    return False

def get_or_create_account(name):
    try:
        # Look for an account we have cached
        account = username_mapping[name]
    except KeyError:
        # See if there's a previously imported account
        account = list(Account._query(Account.c.ob_account_name == name, data=True))
        if len(account) == 1:
            account = account[0]
        elif len(account) > 1:
            print " Got more than one account for OB username '%s', select one below:" % name
            for i in range(len(account)):
                email = account[i].email if hasattr(account[i], 'email') else ''
                print "  %d. %s, %s" % (i, account[i].name, email)
            i += 1
            print "  %d. Create new" % i
            i += 1
            print "  %d. None, abort" % i
            
            max_choice = i
            choice = -1
            while choice < 0 or choice > max_choice:
                choice = raw_input("Enter selection: ")
                try:
                    choice = int(choice)
                except ValueError:
                    choice = -1
            if choice in range(len(account)):
                account = account[choice - 1]
            elif choice == max_choice:
                raise Exception("Aborting")
            else:
                # Fall through to code below
                account = None
        else:
            # Try derivatives of the name that may exist
            candidates = (
                name,
                name.replace(' ', ''),
                name.replace(' ', '_')
            )

            for candidate in candidates:
                try:
                    account = Account._by_name(candidate)
                except NotFound:
                    continue

                if account:
                    if not dryrun:
                        account.ob_account_name = name
                        account._commit()
                    break

        # No account found, create a new one
        if not account:
            account = create_account(name)

        username_mapping[name] = account

    return account

def create_account(full_name):
    name = full_name.replace(' ', '_')
    retry = 2 # First retry will by name2
    username = name
    while True:
        # Create a new account
        try:
            if dryrun:
                try:
                    account = Account._by_name(username)
                    if account:
                        raise AccountExists
                except NotFound:
                    account = FakeAccount()
                    account.name = username
            else:
                account = register(username, generate_password(), None)
                account.ob_account_name = full_name
                account._commit()
        except AccountExists:
            # This username is taken, generate another, but first limit the retries
            if retry > MAX_RETRIES:
                raise StandardError("Unable to create account for '%s' after %d attempts" % (full_name, retry - 1))
        else:
            return account
        username = "%s%d" % (name, retry)
        retry += 1

def process_comments_on_post(post, comments):
    for comment in comments:
        if comment_exists(post, comment):
            continue

        # Prepare data for import
        ip = '127.0.0.1'
        naive_date = datetime.datetime.strptime(comment['dateCreated'], DATE_FORMAT)
        local_date = INPUT_TIMEZONE.localize(naive_date, is_dst=False) # Pick the non daylight savings time
        utc_date = local_date.astimezone(pytz.utc)

        # Determine account to use for this comment
        account = get_or_create_account(comment['author'])

        if not dryrun:
            # Create new comment
            new_comment, inbox_rel = Comment._new(account, post, None, comment['body'], ip, date=utc_date)
            new_comment.is_html = True
            new_comment.ob_imported = True
            new_comment._commit()

        print " Imported as '%s' %s" % (account.name, comment_excerpt(comment))

re_strip_path = re.compile(r'^/overcomingbias')
def adjust_permalink(permalink):
    """Transform:
    http://robinhanson.typepad.com/overcomingbias/2008/12/evolved-desires.html
    into:
    http://www.overcomingbias.com/2008/12/evolved-desires.html"""

    # Adjust the permalink to match those that were imported
    (scheme, host, path, query, fragment) = urlparse.urlsplit(permalink)
    host = 'www.overcomingbias.com'
    path = re_strip_path.sub('', path, 1)

    return urlparse.urlunsplit((scheme, host, path, query, fragment))

def import_missing_comments(filename, apply_changes=False):
    """Imports the comments from the supplied YAML"""
    missing_comments = yaml.load(open(filename), Loader=yaml.CLoader)
    global dryrun
    dryrun = not apply_changes

    total_posts = len(missing_comments)
    post_count = 0
    for post in missing_comments:
        if post['author'] != 'Eliezer Yudkowsky':
            # print "Skipping non-EY post (%s): %s" % (post['author'], post['permalink'])
            continue

        ob_permalink = adjust_permalink(post['permalink'])

        # Attempt to retrieve the post that was imported into Less Wrong
        imported_post = list(Link._query(Link.c.ob_permalink == ob_permalink, data=True))
        if len(imported_post) < 1:
            print "Unable to retrieve imported post: %s" % ob_permalink
            continue
        elif len(imported_post) > 1:
            print "Got more than one result for: %s" % ob_permalink
            raise Exception
        else:
            imported_post = imported_post[0]

        post_count += 1
        print "Importing (%d of %d) comments on: %s" % (post_count, total_posts, imported_post.canonical_url)
        process_comments_on_post(imported_post, post['comments'])

