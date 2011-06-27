# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################
from r2.lib.utils import Storage
from pylons.i18n import _
from copy import copy

error_list = dict((
        ('NO_URL', _('Url required')),
        ('BAD_URL', _('You should check that url')),
        ('NO_TITLE', _('Title required')),
        ('TITLE_TOO_LONG', _('Title too long')),
        ('LOCATION_TOO_LONG', _('Location is too long')),
        ('COMMENT_TOO_LONG', _('Comment too long')),
        ('BAD_CAPTCHA', _('Incorrect, try again')),
        ('BAD_USERNAME', _('Invalid user name')),
        ('BAD_USERNAME_SHORT', _('Username is too short')),
        ('BAD_USERNAME_LONG', _('Username is too long')),
        ('BAD_USERNAME_CHARS', _('Username may not contain special characters')),
        ('USERNAME_TAKEN', _('That username is already taken')),
        ('NO_THING_ID', _('Id not specified')),
        ('NOT_AUTHOR', _("Only the author can do that")),
        ('BAD_COMMENT', _('Please enter a comment')),
        ('BAD_PASSWORD', _('Invalid password')),
        ('WRONG_PASSWORD', _('Incorrect password')),
        ('BAD_PASSWORD_MATCH', _('Passwords do not match')),
        ('NO_NAME', _('Please enter a name')),
        ('NO_EMAIL', _('Please enter an email address')),
        ('NO_EMAIL_FOR_USER', _('No email address for that user')),
        ('NO_MESSAGE', _('Please enter a message')),
        ('NO_TO_ADDRESS', _('Please enter a to address')),
        ('NO_MSG_BODY', _('Please enter a message')),
        ('NO_SUBJECT', _('Please enter a subject')),
        ('USER_DOESNT_EXIST', _("That user doesn't exist")),
        ('NO_USER', _('Please enter a username')),
        ('INVALID_PREF', "that preference isn't valid"),
        ('BAD_NUMBER', _("That number isn't in the right range")),
        ('ALREADY_SUB', _("That link has already been submitted")),
        ('SUBREDDIT_EXISTS', _('That category already exists')),
        ('SUBREDDIT_NOEXIST', _('That category doesn\'t exist')),
        ('SUBREDDIT_FORBIDDEN', _("You don't have permission to submit to that category.")),
        ('BAD_SR_NAME', _('That name isn\'t going to work')),
        ('RATELIMIT', _('You are trying to submit too fast. try again in %(time)s.')),
        ('EXPIRED', _('Your session has expired')),
        ('DRACONIAN', _('You must accept the terms first')),
        ('BANNED_IP', "IP banned"),
        ('BANNED_DOMAIN', "Domain banned"),
        ('BAD_CNAME', "that domain isn't going to work"),
        ('USED_CNAME', "that domain is already in use"),
        ('INVALID_OPTION', _('That option is not valid')),
        ('DESC_TOO_LONG', _('Description is too long')),
        ('CHEATER', 'what do you think you\'re doing there?'),
        ('BAD_EMAILS', _('The following emails are invalid: %(emails)s')),
        ('NO_EMAILS', _('Please enter at least one email address')),
        ('TOO_MANY_EMAILS', _('Please only share to %(num)s emails at a time.')),
        ('NO_LOCATION', _('You must supply a location')),
        ('NO_DATE', _('The time and date of the meetup is required')),
        ('INVALID_DATE', _('Must be a valid date and time')),
        ('NO_DESCRIPTION', _('You must supply a description')),
        ('CANNOT_DELETE', _('Cannot delete that comment')),
    ))
errors = Storage([(e, e) for e in error_list.keys()])

class Error(object):
    #__slots__ = ('name', 'message')
    def __init__(self, name, i18n_message, msg_params):
        self.name = name
        self.i18n_message = i18n_message
        self.msg_params = msg_params
        
    @property
    def message(self):
        return _(self.i18n_message) % self.msg_params

    def __iter__(self):
         #yield ('num', self.num)
        yield ('name', self.name)
        yield ('message', _(self.message))

    def __repr__(self):
        return '<Error: %s>' % self.name

class ErrorSet(object):
    def __init__(self):
        self.errors = {}

    def __contains__(self, error_name):
        return self.errors.has_key(error_name)

    def __getitem__(self, name):
        return self.errors[name]

    def __repr__(self):
        return "<ErrorSet %s>" % list(self)

    def __iter__(self):
        for x in self.errors:
            yield x
        
    def _add(self, error_name, msg, msg_params = {}):
        self.errors[error_name] = Error(error_name, msg, msg_params)
        
    def add(self, error_name, msg_params = {}):
        msg = error_list[error_name]
        self._add(error_name,  msg, msg_params = msg_params)

    def remove(self, error_name):
        if self.errors.has_key(error_name):
            del self.errors[error_name]

class UserRequiredException(Exception): pass
