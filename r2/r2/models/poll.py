from __future__ import with_statement
import re
import datetime
from pylons import c, g, request
from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, CreationError
from account import Account
from r2.lib.utils import to36, median
from r2.lib.filters import safemarkdown
pages = None  # r2.lib.pages imported dynamically further down


class PollError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


poll_re = re.compile(r"""
    \[\s*poll\s*                                   # [poll] or [polltype]
        (?::\s* ([^\]]*?) )?
    \s*\]
    ((?:\s* {\s*[^}]+\s*} )*)                        # Poll options enclosed in curly braces
    """, re.VERBOSE)
poll_options_re = re.compile(r"""
    {\s*([^}]+)\s*}
    """, re.VERBOSE)
pollid_re = re.compile(r"""
    \[\s*pollid\s*:\s*([a-zA-Z0-9]+)\s*\]
    """, re.VERBOSE)
scalepoll_re = re.compile(r"""^
    \s*([^.]+)\s*(\.{2,})\s*([^.]+)\s*
    $""", re.VERBOSE)


def parsepolls(text, thing, dry_run = False):
    """
    Look for poll markup syntax, ie "[poll:polltype]{options}". Parse it,
    create a poll object, and replace the raw syntax with "[pollid:123]".
    `PollError` is raised if there are any errors in the syntax.

    :param dry_run: If true, the syntax is still checked, but no database objects are created.
    """

    def checkmatch(match):
        optionsText = match.group(2)
        options = poll_options_re.findall(optionsText)
        poll = createpoll(thing, match.group(1), options, dry_run = dry_run)
        pollid = "" if dry_run else str(poll._id)
        return "[pollid:" + pollid + "]"

    return re.sub(poll_re, checkmatch, text)


def getpolls(text):
    polls = []
    matches = re.findall(pollid_re, text)
    for match in matches:
        try:
            pollid = int(str(match))
            polls.append(pollid)
        except: pass
    return polls

def containspolls(text):
    return bool(re.match(poll_re, text) or re.match(pollid_re, text))


# Look for poll IDs in a comment/article, like "[pollid:123]", find the
# matching poll in the database, and convert it into an HTML implementation
# of that poll. If there was at least one poll, puts poll options ('[]Vote
# Anonymously [Submit]/[View Results] [Raw Data]') at the bottom
def renderpolls(text, thing):
    polls_not_voted = []
    polls_voted = []
    oldballots = []

    def checkmatch(match):
        pollid = match.group(1)
        try:
            poll = Poll._byID(pollid, True)
            if poll.thingid != thing._id:
                return "Error: Poll belongs to a different comment"

            if poll.user_has_voted(c.user):
                polls_voted.append(pollid)
                return poll.render_results()
            else:
                polls_not_voted.append(pollid)
                return poll.render()
        except NotFound:
            return "Error: Poll not found!"

    text = re.sub(pollid_re, checkmatch, text)

    if polls_voted or polls_not_voted:
        voted_on_all = not polls_not_voted
        page = _get_pageclass('PollWrapper')(thing, text, voted_on_all)
        text = page.render('html')

    return text

def pollsandmarkdown(text, thing):
    ret = renderpolls(safemarkdown(text), thing)
    return ret


def createpoll(thing, polltype, args, dry_run = False):
    poll = Poll.createpoll(thing, polltype, args, dry_run = dry_run)
    if g.write_query_queue:
        queries.new_poll(poll)
    return poll


def exportvotes(pollids):
    csv_rows = []
    aliases = {'next_alias': 1}
    for pollid in pollids:
        poll = Poll._byID(pollid)
        ballots = poll.get_ballots()
        for ballot in ballots:
            row = ballot.export_row(aliases)
            csv_rows.append(row)
    return exportheader() + '\n'.join(csv_rows)

def exportheader():
    return """#
# Exported poll results from Less Wrong
# Columns: user, pollid, response, date
# user is either a username or a number (if the 'voted anonymously' button was
# checked). Anonymous user numbers are shared between poll questions asked in a
# single comment, but not between comments.
# pollid is a site-wide unique identifier of the poll.
# response is the user's answer to the poll. For multiple-choice polls, this is
# the index of their choice, starting at zero. For scale polls, this is the
# distance of their choice from the left, starting at zero. For probability and
# numeric polls, this is a number.
#
"""


def _get_pageclass(name):
    # sidestep circular import issues
    global pages
    if not pages:
        from r2.lib import pages
    return getattr(pages, name)


class PollType:
    ballot_class = None
    results_class = None

    def render(self, poll):
        return _get_pageclass(self.ballot_class)(poll).render('html')

    def render_results(self, poll):
        return _get_pageclass(self.results_class)(poll).render('html')

    def _check_num_choices(self, num):
        if num < 2:
            raise PollError('Polls must have at least two choices')
        if num > g.poll_max_choices:
            raise PollError('Polls cannot have more than {0} choices'.format(g.poll_max_choices))

    def _check_range(self, num, func, min, max, message):
        try:
            num = func(num)
            if min <= num <= max:
                return str(num)
        except:
             pass
        raise PollError(message)


class MultipleChoicePoll(PollType):
    ballot_class = 'MultipleChoicePollBallot'
    results_class = 'MultipleChoicePollResults'

    def init_blank(self, poll):
        self._check_num_choices(len(poll.choices))
        poll.votes_for_choice = [0 for _ in poll.choices]

    def add_response(self, poll, response):
        poll.votes_for_choice[int(response)] = poll.votes_for_choice[int(response)] + 1

    def validate_response(self, poll, response):
        return self._check_range(response, int, 0, len(poll.choices) - 1, 'Invalid choice')


class ScalePoll(PollType):
    ballot_class = 'ScalePollBallot'
    results_class = 'ScalePollResults'

    def init_blank(self, poll):
        parsed_poll = re.match(scalepoll_re, poll.polltypestring)
        poll.scalesize = len(parsed_poll.group(2))
        poll.leftlabel = parsed_poll.group(1)
        poll.rightlabel = parsed_poll.group(3)

        self._check_num_choices(poll.scalesize)
        poll.votes_for_choice = [0 for _ in range(poll.scalesize)]

    def add_response(self, poll, response):
        poll.votes_for_choice[int(response)] = poll.votes_for_choice[int(response)] + 1

    def validate_response(self, poll, response):
        return self._check_range(response, int, 0, poll.scalesize - 1, 'Invalid choice')


class NumberPoll(PollType):
    ballot_class = 'NumberPollBallot'
    results_class = 'NumberPollResults'

    def init_blank(self, poll):
        poll.sum = 0
        poll.median = 0

    def add_response(self, poll, response):
        responsenum = float(response)
        poll.sum += responsenum
        responses = [float(ballot.response) for ballot in poll.get_ballots()]
        responses.sort()
        poll.median = median(responses)
        
    def validate_response(self, poll, response):
        return self._check_range(response, float, -2**64, 2**64, 'Invalid number')


class ProbabilityPoll(NumberPoll):
    ballot_class = 'ProbabilityPollBallot'
    results_class = 'ProbabilityPollResults'

    def validate_response(self, poll, response):
        return self._check_range(response, float, 0, 1, 'Probability must be between 0 and 1')


class Poll(Thing):
    @classmethod
    def createpoll(cls, thing, polltypestring, options, dry_run = False):
        assert dry_run == (thing is None)

        polltype = cls.normalize_polltype(polltypestring)

        poll = cls(thingid = thing and thing._id,
                   polltype = polltype,
                   polltypestring = polltypestring,
                   choices = options)

        polltype_class = poll.polltype_class()
        if not polltype_class:
            raise PollError(u"Invalid poll type '{0}'".format(polltypestring))

        poll.init_blank()

        if not dry_run:
            thing.has_polls = True
            poll._commit()

        return poll

    @classmethod
    def normalize_polltype(self, polltype):
        #If not specified, default to multiplechoice
        if not polltype:
            return 'multiplechoice'
        
        polltype = polltype.lower()
        
        #If the poll type has a dot in it, then it's a scale, like 'agree.....disagree'
        if re.match(scalepoll_re, polltype):
            return 'scale'
        
        #Check against lists of synonyms
        if polltype in {'choice':1, 'c':1, 'list':1}:
            return 'multiplechoice'
        elif polltype in {'probability':1, 'prob':1, 'p':1, 'chance':1, 'likelihood':1}:
            return 'probability'
        elif polltype in {'number':1, 'numeric':1, 'num':1, 'n':1, 'float':1, 'double':1}:
            return 'number'
        else:
            return 'invalid'

    def polltype_class(self):
        if self.polltype == 'multiplechoice':
            return MultipleChoicePoll()
        elif self.polltype == 'scale' :
            return ScalePoll()
        elif self.polltype == 'probability' :
            return ProbabilityPoll()
        elif self.polltype == 'number':
            return NumberPoll()
        else:
            return None
    
    def init_blank(self):
        self.num_votes = 0
        self.polltype_class().init_blank(self)
        
    def add_response(self, response):
        self.num_votes = self.num_votes + 1
        self.polltype_class().add_response(self, response)
        self._commit()
    
    def validate_response(self, response):
        return self.polltype_class().validate_response(self, response)
    
    def render(self):
        return self.polltype_class().render(self)
    
    def render_results(self):
        return self.polltype_class().render_results(self)
    
    def user_has_voted(self, user):
        if not c.user_is_loggedin:
            return False
        oldballots = self.get_user_ballot(user)
        return (len(oldballots) > 0)
    
    def get_user_ballot(poll, user):
        return list(Ballot._query(Ballot.c._thing1_id == user._id,
                                  Ballot.c._thing2_id == poll._id,
                                  data = True))


    def get_ballots(self):
        return list(Ballot._query(Ballot.c._thing2_id == self._id,
                                  data = True))
    
    def num_votes_for(self, choice):
        if self.votes_for_choice:
            return self.votes_for_choice[choice]
        else:
            raise TypeError

    def bar_length(self, choice, max_length):
        max_votes = max(self.votes_for_choice)
        if max_votes == 0:
            return 0
        return int(float(self.num_votes_for(choice)) / max_votes * max_length)

    def fraction_for(self, choice):
        return float(self.num_votes_for(choice)) / self.num_votes * 100
    
    def rendered_percentage_for(self, choice):
        return str(int(round(self.fraction_for(choice)))) + "%"
    
    #Get the total number of votes on this poll as a correctly-pluralized noun phrase, ie "123 votes" or "1 vote"
    def num_votes_string(self):
        if self.num_votes == 1:
            return "1 vote"
        else:
            return str(self.num_votes) + " votes"
    
    def get_property(self, property):
        if property == 'mean':
            return self.sum / self.num_votes
        elif property == 'median':
            return self.median


class Ballot(Relation(Account, Poll)):
    @classmethod
    def submitballot(cls, user, comment, pollobj, response, anonymous, ip, spam):
        with g.make_lock('voting_on_%s' % pollobj._id):
            pollid = pollobj._id
            oldballot = list(cls._query(cls.c._thing1_id == user._id,
                                        cls.c._thing2_id == pollid))
            if len(oldballot):
                raise PollError('You already voted on this poll')

            ballot = Ballot(user, pollobj, response)
            ballot.ip = ip
            ballot.anonymous = anonymous
            ballot.date = datetime.datetime.now().isoformat()
            ballot.response = response
            ballot._commit()
            pollobj.add_response(response)
        return ballot
    
    def export_row(self, aliases):
        userid = self._thing1_id
        pollid = self._thing2_id
        if hasattr(self, 'anonymous') and self.anonymous:
            if not userid in aliases:
                aliases[userid] = aliases['next_alias']
                aliases['next_alias'] = aliases['next_alias'] + 1
            username = aliases[userid]
        else:
            username = Account._byID(userid).name
        return "\"{0}\",\"{1}\",\"{2}\",\"{3}\"".format(username, pollid, self.response, self.date)

