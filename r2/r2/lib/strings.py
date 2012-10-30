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
"""
Module for maintaining long or commonly used translatable strings,
removing the need to pollute the code with lots of extra _ and
ungettext calls.  Also provides a capacity for generating a list of
random strings which can be different in each language, though the
hooks to the UI are the same.
"""

import helpers as h
from pylons.i18n import _, ungettext
import random

__all__ = ['StringHandler', 'strings', 'PluralManager', 'plurals',
           'Score', 'rand_strings']

# here's where all of the really long site strings (that need to be
# translated) live so as not to clutter up the rest of the code.  This
# dictionary is not used directly but rather is managed by the single
# StringHandler instance strings
string_dict = dict(

    banned_by = "banned by %s",
    banned    = "banned",
    reports   = "reports: %d",
    
    # this accomodates asian languages which don't use spaces
    number_label = _("%d %s"),

    # this accomodates asian languages which don't use spaces
    float_label = _("%5.3f %s"),

    # this is for Japanese which treats people counds differently
    person_label = _("%(num)d %(persons)s"),

    firsttext = _("Less Wrong is a community blog devoted to refining the art of human rationality. Please visit our [About](/about-less-wrong/) page for more information."),

    already_submitted = _("That link has already been submitted, but you can try to [submit it again](%s)."),

    multiple_submitted = _("That link has been submitted to multiple categories. you can try to [submit it again](%s)."),

    user_deleted = _("Your account has been deleted, but we won't judge you for it."),

    cover_msg      = _("You'll need to login or register to do that"),
    cover_disclaim = _("(Don't worry, it only takes a few seconds)"),

    legal = _("I understand and agree that registration on or use of this site constitutes agreement to its %(user_agreement)s and %(privacy_policy)s."),
    
    friends = _('To view Less Wrong with only submissions from your friends, use [lesswrong.com/r/friends](%s)'),

    msg_add_friend = dict(
        friend = None,
        moderator = _("You have been added as a moderator to [%(title)s](%(url)s)."),
        contributor = _("You have been added as a contributor to [%(title)s](%(url)s)."),
        banned = _("You have been banned from posting to [%(title)s](%(url)s).")
        ),

    subj_add_friend = dict(
        friend = None,
        moderator = _("You are a moderator"),
        contributor = _("You are a contributor"),
        banned = _("You've been banned")
        ),
    
    sr_messages = dict(
        empty =  _('You have not subscribed to any categories.'),
        subscriber =  _('Below are the categories you have subscribed to'),
        contributor =  _('Below are the categories that you have contributor access to.'),
        moderator = _('Below are the categories that you have moderator access to.')
        ),
    
    sr_subscribe =  _('Click the ![add](/static/sr-add-button.png) or ![remove](/static/sr-remove-button.png) buttons to choose which categories appear on your front page.'),

    searching_a_reddit = _('You\'re searching within the [%(reddit_name)s](%(reddit_link)s) category. '+
                           'you can also search within [all categories](%(all_reddits_link)s)'),

    css_validator_messages = dict(
        broken_url = _('"%(brokenurl)s" is not a valid URL'),
        invalid_property = _('"%(cssprop)s" is not a valid CSS property'),
        invalid_val_for_prop = _('"%(cssvalue)s" is not a valid value for CSS property "%(cssprop)s"'),
        too_big = _('Too big. keep it under %(max_size)dkb'),
        syntax_error = _('Syntax error: "%(syntaxerror)s"'),
        no_imports = _('@imports are not allowed'),
        invalid_property_list = _('Invalid CSS property list "%(proplist)s"'),
        unknown_rule_type = _('Unknown CSS rule type "%(ruletype)s"')
    ),
    
    submit_box_text = _('To anything interesting: news article, blog entry, video, picture...'),
    permalink_title = _("%(author)s comments on %(title)s - %(site)s"),
    link_info_title = _("%(title)s - %(site)s"),
    show_meetup_title = _("%(title)s - %(site)s"),
    not_enough_downvote_karma = _('You do not have enough karma to downvote right now. You need %d more %s.')
)

class StringHandler(object):
    """Class for managing long translatable strings.  Allows accessing
    of strings via both getitem and getattr.  In both cases, the
    string is passed through the gettext _ function before being
    returned."""
    def __init__(self, **sdict):
        self.string_dict = sdict

    def __getitem__(self, attr):
        try:
            return self.__getattr__(attr)
        except AttributeError:
            raise KeyError
    
    def __getattr__(self, attr):
        rval = self.string_dict[attr]
        if isinstance(rval, (str, unicode)):
            return _(rval)
        elif isinstance(rval, dict):
            return dict((k, _(v)) for k, v in rval.iteritems())
        else:
            raise AttributeError

strings = StringHandler(**string_dict)


def P_(x, y):
    """Convenience method for handling pluralizations.  This identity
    function has been added to the list of keyword functions for babel
    in setup.cfg so that the arguments are translated without having
    to resort to ungettext and _ trickery."""
    return (x, y)

class PluralManager(object):
    """String handler for dealing with pluralizable forms.  plurals
    are passed in in pairs (sing, pl) and can be accessed via
    self.sing and self.pl.

    Additionally, calling self.N_sing(n) (or self.N_pl(n)) (where
    'sing' and 'pl' are placeholders for a (sing, pl) pairing) is
    equivalent to ungettext(sing, pl, n)
    """
    def __init__(self, plurals):
        self.string_dict = {}
        for s, p in plurals:
            self.string_dict[s] = self.string_dict[p] = (s, p)

    def __getattr__(self, attr):
        if attr.startswith("N_"):
            a = attr[2:]
            rval = self.string_dict[a]
            return lambda x: ungettext(rval[0], rval[1], x)
        else:
            rval = self.string_dict[attr]
            n = 1 if attr == rval[0] else 5
            return ungettext(rval[0], rval[1], n)

plurals = PluralManager([P_("comment",     "comments"),
                         P_("point",       "points"),
                         
                         # things
                         P_("link",        "links"),
                         P_("comment",     "comments"),
                         P_("message",     "messages"),
                         P_("subreddit",   "subreddits"),
                         
                         # people
                         P_("subscriber",  "subscribers"),
                         P_("contributor", "contributors"),
                         P_("moderator",   "moderators"),
                         
                         # time words
                         P_("milliseconds","milliseconds"),
                         P_("second",      "seconds"),
                         P_("minute",      "minutes"),
                         P_("hour",        "hours"),
                         P_("day",         "days"),
                         P_("month",       "months"),
                         P_("year",        "years"),
])


class Score(object):
    """Convienience class for populating '10 points' in a traslatible
    fasion, used primarily by the score() method in printable.html"""
    @staticmethod
    def number_only(pair):
        total = pair[0] - pair[1]
        return {'label': str(max(total, 0)), 'hover': ''}

    @staticmethod
    def signed_number(pair):
        total = pair[0] - pair[1]
        return {
            'label': str(total),
            'hover': '{0:.0%} positive'.format(sum(pair) and float(pair[0]) / sum(pair)),
        }

    @staticmethod
    def points(pair):
        total = pair[0] - pair[1]
        return {
            'label': strings.number_label % (total, plurals.N_points(total)),
            'hover': '{0:.0%} positive'.format(sum(pair) and float(pair[0]) / sum(pair)),
        }

    @staticmethod
    def safepoints(pair):
        total = pair[0] - pair[1]
        return {
            'label': strings.number_label % (max(total, 0), plurals.N_points(total)),
            'hover': '',
        }

    @staticmethod
    def subscribers(pair):
        total = pair[0] - pair[1]
        return {
            'label': strings.person_label % {'num': total,
                                             'persons': plurals.N_subscribers(total)},
            'hover': '',
        }

    @staticmethod
    def none(pair):
        return {'label': '', 'hover': ''}


def fallback_trans(x):
    """For translating placeholder strings the user should never see
    in raw form, such as 'funny 500 message'.  If the string does not
    translate in the current language, falls back on the 'en'
    translation that we've hopefully already provided"""
    t = _(x)
    if t == x:
        l = h.get_lang()
        h.set_lang('en', graceful_fail = True)
        t = _(x)
        if l and l[0] != 'en':
            h.set_lang(l[0])
    return t

class RandomString(object):
    """class for generating a translatable random string that is one
    of n choices.  The 'description' field passed to the constructor
    is only used to generate labels for the translation interface.

    Unlike other translations, this class is accessed directly by the
    translator classes and side-step babel.extract_messages.
    Untranslated, the strings return are of the form 'description n+1'
    for the nth string.  The user-facing versions of these strings are
    therefore completely determined by their translations."""
    def __init__(self, description, num):
        self.desc = description
        self.num = num
    
    def get(self, quantity = 0):
        """Generates a list of 'quantity' random strings.  If quantity
        < self.num, the entries are guaranteed to be unique."""
        l = []
        possible = []
        for x in range(max(quantity, 1)):
            if not possible:
                possible = range(self.num)
            irand = random.choice(possible)
            possible.remove(irand)
            l.append(fallback_trans(self._trans_string(irand)))

        return l if len(l) > 1 else l[0]

    def _trans_string(self, n):
        """Provides the form of the string that is actually translated by gettext."""
        return "%s %d" % (self.desc, n+1)

    def __iter__(self):
        for i in xrange(self.num):
            yield self._trans_string(i)
                   

class RandomStringManager(object):
    """class for keeping randomized translatable strings organized.
    New strings are added via add, and accessible by either getattr or
    getitem using the short name passed to add."""
    def __init__(self):
        self.strings = {}

    def __getitem__(self, attr):
        return self.strings[attr].get()

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError

    def get(self, attr, quantity = 0):
        """Convenience method for getting a list of 'quantity' strings
        from the RandomString named 'attr'"""
        return self.strings[attr].get(quantity)

    def add(self, name, description, num):
        """create a new random string accessible by 'name' in the code
        and explained in the translation interface with 'description'."""
        self.strings[name] = RandomString(description, num)

    def __iter__(self):
        """iterator primarily used by r2.lib.translations to fetch the
        list of random strings and to iterate over their names to
        insert them into the resulting .po file for a given language"""
        return self.strings.iteritems()

rand_strings = RandomStringManager()

rand_strings.add('sadmessages',   "Funny 500 page message", 1)
rand_strings.add('create_reddit', "Reason to create a reddit", 20)
