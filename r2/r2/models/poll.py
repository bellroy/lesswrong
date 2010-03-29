import re
from pylons import c, g, request
from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, CreationError
from account import Account
from r2.lib.utils import to36
from r2.lib.wrapped import Wrapped
from r2.lib.pages import MultipleChoicePollBallot, MultipleChoicePollResults, ScalePollBallot, ScalePollResults, ProbabilityPollBallot, ProbabilityPollResults, NumberPollBallot, NumberPollResults
from r2.lib.filters import safemarkdown

poll_re = re.compile(r"""
    \[\s*poll\s*(?::\s*([a-zA-Z0-9_\.]*))?\s*\]    # Starts with [poll] or [poll:polltype]
    ((?:\s*{[^}]+})*)                             # Poll options enclosed in curly braces
    """, re.VERBOSE)
poll_options_re = re.compile(r"""
    {([^}]+)}
    """, re.VERBOSE)

def parsepolls(text, thing):
    # Look for markup that looks like a poll specification, ie "[poll:polltype]{poll options}",
    # parse the descriptions and create poll objects, and replace the specifications with IDs,
    # ie "[pollid:123]". Returns the adjusted text.
    def checkmatch(match):
        optionsText = match.group(2)
        options = poll_options_re.findall(optionsText)
        pollid = createpoll(thing, match.group(1), options)
        return "[pollid:" + str(pollid) + "]"

    return re.sub(poll_re, checkmatch, text)

pollid_re = re.compile(r"""
    \[pollid:([a-zA-Z0-9]*)\]
    """, re.VERBOSE)

def pollsandmarkdown(text, commentid):
    ret = renderpolls(safemarkdown(text), commentid)
    return ret

# Look for poll IDs in a comment/article, like "[pollid:123]", find the
# matching poll in the database, and convert it into an HTML implementation
# of that poll. If there was at least one poll, puts poll options ('[]Vote
# Anonymously [Submit]/[View Results] [Raw Data]') at the bottom
def renderpolls(text, commentid):
    polls_not_voted = []
    polls_voted = []
    oldballots = []
    
    def checkmatch(match):
        pollid = match.group(1)
        try:
            poll = Poll._byID(pollid, True)
            if poll.thingid != commentid:
                return "Error: Poll belongs to a different comment"
            
            if(poll.user_has_voted(c.user)):
                polls_voted.append(pollid)
                return poll.render_results()
            else:
                polls_not_voted.append(pollid)
                return poll.render()
        except NotFound:
            return "Error: Poll not found!"
    
    rendered_body = re.sub(pollid_re, checkmatch, text)
    
    if(len(polls_not_voted) > 0):
        return wrap_ballot(commentid, rendered_body)
    elif(len(polls_voted) > 0):
        return wrap_results(commentid, rendered_body)
    else:
        return rendered_body

def getpolls(text):
    polls = []
    matches = re.findall(pollid_re, text)
    if not matches:
        return []
    for match in matches:
        try:
            pollid = int(str(match))
            polls.append(pollid)
        except: pass
    return polls

def containspolls(text):
    if re.match(poll_re, text):
        return True
    elif re.match(pollid_re, text):
        return True
    else:
        return False

def wrap_ballot(commentid, body):
    return """
        <form id="{0}" method="post" action="/api/submitballot" onsubmit="return submitballot(this)">"
            {1}
        <button type="Submit">Submit</button>"
        </form>""".format(to36(commentid), body)

def wrap_results(commentid, body):
     return """{0} <a href="/api/rawdata?thing={1}">Raw poll data</a>""".format(body, to36(commentid))

def createpoll(thing, polltype, args):
    poll = Poll.createpoll(thing, polltype, args)
    if g.write_query_queue:
        queries.new_poll(poll)
    return poll._id

def exportvotes(pollids):
    csv_rows = []
    for pollid in pollids:
        poll = Poll._byID(pollid)
        ballots = poll.get_ballots()
        for ballot in ballots:
            row = ballot.export_row()
            csv_rows.append(row)
    return exportheader() + '\n'.join(csv_rows)

def exportheader():
    return """#
#Exported poll results from Less Wrong
#Columns: user, pollid, response
#
"""

scalepoll_re = re.compile(r"""
    ([a-zA-Z0-9_]+)(\.\.+)([a-zA-Z0-9_]+)
    """, re.VERBOSE)

class MultipleChoicePoll:
    def init_blank(self, poll):
        poll.votes_for_choice = []
        for choice in poll.choices:
            poll.votes_for_choice.append(0)
    def add_response(self, poll, response):
        poll.votes_for_choice[int(response)] = poll.votes_for_choice[int(response)] + 1
    def validate_response(self, poll, response):
        try:
            choiceindex = int(response)
            return (choiceindex >= 0 and choiceindex < len(choices))
        except:
             return False
    def render(self, poll):
        return MultipleChoicePollBallot(poll).render('html')
    def render_results(self, poll):
        return MultipleChoicePollResults(poll).render('html')

class ScalePoll:
    def init_blank(self, poll):
        parsed_poll = re.match(scalepoll_re, poll.polltypestring)
        poll.scalesize = len(parsed_poll.group(2))
        poll.leftlabel = parsed_poll.group(1)
        poll.rightlabel = parsed_poll.group(3)
        poll.votes_for_choice = []
        for choice in range(poll.scalesize):
            poll.votes_for_choice.append(0)
    def add_response(self, poll, response):
        poll.votes_for_choice[int(response)] = poll.votes_for_choice[int(response)] + 1
    def validate_response(self, poll, response):
        try:
            choiceindex = int(response)
            return (choiceindex >= 0 and choiceindex < scalesize)
        except:
             return False
    def render(self, poll):
        return ScalePollBallot(poll).render('html')
    def render_results(self, poll):
        return ScalePollResults(poll).render('html')

class NumberPoll:
    def init_blank(self, poll):
        poll.sum = 0
        poll.median = 0
    def add_response(self, poll, response):
        responsenum = float(response)
        poll.sum = poll.sum + responsenum
        responses = []
        for ballot in poll.get_ballots():
            responses.append(float(ballot.response))
        responses.append(responsenum)
        responses.sort()
        if len(responses) % 2:
            poll.median = responses[len(responses)/2]
        else:
            poll.median = (float(responses[len(responses)/2]) + float(responses[len(responses)/2 - 1])) / 2
        
    def validate_response(self, poll, response):
        try:
            response = float(response)
            return True
        except:
             return False
    def render(self, poll):
        return NumberPollBallot(poll).render('html')
    def render_results(self, poll):
        return NumberPollResults(poll).render('html')

class ProbabilityPoll(NumberPoll):
    def validate_response(self, poll, response):
        try:
            prob = float(response)
            return (response >= 0 and response <= 1)
        except:
             return False
    def render(self, poll):
        return ProbabilityPollBallot(poll).render('html')
    def render_results(self, poll):
        return ProbabilityPollResults(poll).render('html')


class Poll(Thing):
    @classmethod
    def createpoll(cls, thing, polltypestring, options):
        polltype = Poll.normalize_polltype(polltypestring)
        poll = cls(thingid = thing._id,
                   polltype = polltype,
                   polltypestring = polltypestring,
                   choices = options)
        thing.has_polls = True
        poll.init_blank()
        poll._commit()
        return poll
    
    def polltype_class(self):
        polltype = self.polltype
        if(polltype == 'multiplechoice'):
            return MultipleChoicePoll()
        elif(polltype == 'scale'):
            return ScalePoll()
        elif(polltype == 'probability'):
            return ProbabilityPoll()
        elif(polltype == 'number'):
            return NumberPoll()

    @classmethod
    def normalize_polltype(self, polltype):
        #If not specified, default to multiplechoice
        if not polltype or polltype == None or polltype == '':
            return "multiplechoice"
        
        #Make lower-case
        polltype = str(polltype).lower()
        
        #If the poll type has a dot in it, then it's a scale, like 'agree.....disagree'
        if(re.match(scalepoll_re, polltype)):
            return 'scale'
        
        #Check against lists of synonyms
        if(polltype in {'multiplechoice':1, 'choice':1, 'multiple':1, 'list':1}):
            return 'multiplechoice'
        elif(polltype in {'probability':1, 'prob':1, 'p':1, 'likelihood':1}):
            return 'probability'
        elif(polltype in {'number':1, 'numeric':1, 'num':1, 'int':1, 'float':1, 'double':1}):
            return 'number'
        else:
            return 'invalid'
    
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
        if (self.votes_for_choice):
            return self.votes_for_choice[choice]
        else:
            return -1
    
    #Get the total number of votes on this poll as a correctly-pluralized noun phrase, ie "123 votes" or "1 vote"
    def num_votes_string(self):
        if(self.num_votes == 1):
            return "1 vote"
        else:
            return str(self.num_votes) + " votes"
    
    def get_property(self, property):
        if(property == 'mean'):
            return self.sum / self.num_votes
        elif(property == 'median'):
            return self.median

class Ballot(Relation(Account, Poll)):
    @classmethod
    def submitballot(cls, user, comment, pollobj, response, anonymous, ip, spam):
        with g.make_lock('voting_on_%s' % pollobj._id):
            pollid = pollobj._id
            oldballot = list(cls._query(cls.c._thing1_id == user._id,
                                        cls.c._thing2_id == pollid))
            if len(oldballot):
                return
            else:
                ballot = Ballot(user, pollobj, response)
                ballot.ip = ip
                ballot.anonymous = anonymous
                pollobj.add_response(response)
            ballot.response = response
            ballot._commit()
        return ballot
    
    def export_row(self):
        userid = self._thing1_id
        pollid = self._thing2_id
        user = Account._byID(userid)
        return "\"{0}\",\"{1}\",\"{2}\"".format(user.name, pollid, self.response)

