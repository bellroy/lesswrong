#!/usr/bin/env python

"""
This script is run periodically by cron. It scans through a database table of
pending jobs and executes them. A memcache lock is used to ensure that each job
is claimed by only one node. If an exception occurs while running a job, an
error will be logged and the job will remain in the queue to be attempted next
time this script is run.
"""
import re, traceback, urllib2

from sys import stderr
from datetime import datetime, timedelta

from pylons import g

from r2.lib.lock import MemcacheLock
from r2.lib.rancode import random_key
from r2.lib.wiki_account import create_wiki_account
from r2.lib import notify, emailer
from r2.lib.db.thing import NotFound
from r2.models import Account, Meetup, PendingJob

from lxml import etree


class JobProcessor:
    def run(self):
        jobs = PendingJob._query(data=True)

        for job in jobs:
            self.process_job(job)

    def process_job(self, job):
        if job.run_at is not None and job.run_at > datetime.now(g.tz):
            return

        runner = globals().get('job_' + job.action)
        if not runner:
            print >>stderr, 'Unknown job action {0!r}'.format(job.action)
            return

        # If we can't acquire the lock, the job has already been claimed,
        # so we skip it.
        lock = g.make_lock('pending_job_{0}'.format(job._id))
        if not lock.try_acquire():
            return

        try:
            data = job.data or {}
            runner(**data)
        except Exception as ex:
            print >>stderr, 'Exception while running job id {0} ({1}): {2}'.format(
                job._id, job.action, ex)
        else:
            self.mark_as_completed(job)
        finally:
            lock.release()

    def mark_as_completed(self, job):
        job._delete_from_db()


def job_process_new_meetup(meetup_id):
    # Find all users near the meetup who opted to be notified, and add a child
    # job for each of them, so that the scope of any problems is limited.
    # These child jobs will run on the next run-through of this script.
    meetup = Meetup._byID(meetup_id, data=True)
    users = notify.get_users_to_notify_for_meetup(meetup.coords)
    for user in users:
        data = {'username': user.name, 'meetup_id': meetup._id}
        PendingJob.store(None, 'send_meetup_email_to_user', data)


def job_send_meetup_email_to_user(meetup_id, username):
    meetup = Meetup._byID(meetup_id, data=True)
    try:
      user = Account._by_name(username)
      notify.email_user_about_meetup(user, meetup)
    except NotFound:
      # Users can get deleted so ignore if not found
      pass



#Tries to create an account. If connection fails, tries again later.
#After failing twice or getting error code from wiki, sends email to user.
def job_create_wiki_account(name, password, email, attempt):
    tokenmatcher = re.compile('<\?xml version=\"1.0\"\?><api><createaccount token=\"(.*?)\" result=\"needtoken\" /></api>')
    successmatcher = re.compile('<\?xml\sversion="1\.0"\?><api><createaccount.*?result="success"\s/></api>')

    sendpass = False
    if not password:
        password = random_key(6)
        sendpass = True

    try:
        response = create_wiki_account(name, password, email)

        resultxml = etree.fromstring(response)

        if resultxml.find("createaccount") is None and resultxml.find("error").attrib["code"] != 'userexists':
            user = Account._by_name(name)
            emailer.wiki_failed_email(user)
        elif sendpass:
            user = Account._by_name(name)
            emailer.wiki_password_email(user, password)

    except (urllib2.URLError, urllib2.HTTPError):
        if attempt == 0:
            data = {'name' : name, 'password' : password, 'email' : email, 'attempt' : 1}
            time = datetime.now(g.tz) + timedelta(0,15)
            PendingJob.store(time, 'create_wiki_account', data)
        elif attempt == 1:
            data = {'name' : name, 'password' : password, 'email' : email, 'attempt' : 2}
            time = datetime.now(g.tz) + timedelta(0,300)
            PendingJob.store(time, 'create_wiki_account', data)
        elif attempt == 2:
            user = Account._by_name(name)
            emailer.wiki_failed_email(user)
            emailer.simple_email('lesswrong.issues@trikeapps.com',
                                 'contact@lesswrong.com',
                                 'wiki error',
                                 traceback.format_exc())



try:
    JobProcessor().run()
except Exception as ex:
    print >>stderr, 'Critical failure processing job queue: {0}'.format(ex)
