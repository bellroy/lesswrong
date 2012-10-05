#!/usr/bin/env python

"""
This script is run periodically by cron. It scans through a database table of
pending jobs and executes them. A memcache lock is used to ensure that each job
is claimed by only one node. If an exception occurs while running a job, an
error will be logged and the job will remain in the queue to be attempted next
time this script is run.
"""

from datetime import datetime

from pylons import g

from r2.lib.lock import MemcacheLock
from r2.lib import notify
from r2.models import Account, Meetup, PendingJob


class JobProcessor:
    def run(self):
        jobs = PendingJob._query()

        for job in jobs:
            job._safe_load()
            self.process_job(job)

    def process_job(self, job):
        if job.run_at is not None and job.run_at > datetime.now(g.tz):
            return

        runner = globals().get('job_' + job.action)
        if not runner:
            g.log.error('Unknown job action {0!r}'.format(job.action))
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
            g.log.error('Exception while running job id {0} ({1}): {2}'.format(
                job._id, job.action, ex))
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
    user = Account._by_name(username)
    notify.email_user_about_meetup(user, meetup)


try:
    JobProcessor().run()
except Exception as ex:
    g.log.error('Critical failure processing job queue: {0}'.format(ex))
