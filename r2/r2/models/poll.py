import re
from pylons import c, g, request
from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, CreationError
from account import Account
from r2.lib.utils import to36
from r2.lib.db import queries

poll_re = re.compile(r"""
    \[\s*poll\s*(?::([a-zA-Z]*))?\s*\]    # Starts with [poll] or [poll:polltype]
    ((?:\s*{[^}]+})*)                     # Poll options enclosed in curly braces
    """, re.VERBOSE)
poll_options_re = re.compile(r"""
    {([^}]+)}
    """, re.VERBOSE)

def parsepolls(text, thingid):
    # Look for markup that looks like a poll specification, ie "[poll:polltype]{polldescription}",
    # parse the descriptions and create poll objects, and replace the specifications with IDs,
    # ie "[pollid:123]"
    def checkmatch(match):
        optionsText = match.group(2)
        options = poll_options_re.findall(optionsText)
        pollid = createpoll(thingid, match.group(1), options)
        return "[pollid:" + str(pollid) + "]"

    return re.sub(poll_re, checkmatch, text)

pollid_re = re.compile(r"""
    \[pollid:([a-zA-Z0-9]*)\]
    """, re.VERBOSE)

def renderpolls(text, commentid):
    # Look for poll IDs in a comment/article, like "[pollid:123]", find the
    # matching poll in the database, and convert it into an HTML implementation
    # of that poll. If there was at least one poll, puts poll options ('[]Vote
    # Anonymously [Submit]/[View Results] [Raw Data]') at the bottom
    polls_not_voted = []
    polls_voted = []
    oldballots = []
    
    def checkmatch(match):
        pollid = match.group(1)
        try:
            poll = Poll._byID(pollid, True)
            
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
    	return polltemplate(commentid, rendered_body,)
    else:
        return rendered_body

def polltemplate(commentid, body):
    ret = "<form id=\"" + str(commentid) + "\" method=\"post\" action=\"/api/submitballot\" onsubmit=\"return submitballot(this)\">" + body + pollfooter(commentid) + "<button type=\"Submit\">Submit</button><button>Reveal</button></form>"

def pollfooter(commentid):

def createpoll(commentid, polltype, args):
    poll = Poll.createpoll(commentid, polltype, args[0], args[1:])
    if g.write_query_queue:
        queries.new_poll(poll)
    return poll._id

class Poll(Thing):
    @classmethod
    def createpoll(cls, commentid, polltype, description, options):
        poll = cls(commentid = commentid,
                   polltype = polltype,
                   description = description,
                   choices = options)
        poll._commit()
        return poll
    
    def render(self):
        ret = "<form><B>" + self.description + "\n"
        for ii in range(len(self.choices)):
            ret += "<input type=\"radio\" name=\"" + self._id36 + "\" value=\"" + str(ii) + "\">" + self.choices[ii] + "</input>"
        ret += "</B></form>"
        return ret
    
    def render_results(self):
        ballots = list(Ballot._query(Ballot.c._thing2_id == self._id))
        
        sum = 0
        for ballot in ballots:
            sum += int(ballot.response)
        
        return self.description + (" (mean %i)" % (sum/len(ballots)))
    
    def user_has_voted(self, user):
        oldballots = get_user_ballot(user, self)
        return (len(oldballots) > 0)
    
    def get_results(self):
        return get_ballots(self)

class Ballot(Relation(Account, Poll)):
    @classmethod
    def submitballot(cls, user, comment, pollobj, response, ip, spam):
        with g.make_lock('account_%s_balloting' % user._id):
            pollid = pollobj._id
            oldballot = list(cls._query(cls.c._thing1_id == user._id,
                                        cls.c._thing2_id == pollid))
            if len(oldballot):
                ballot = oldballot[0]
            else:
                ballot = Ballot(user, pollobj, response)
                ballot.ip = ip
                #ballot = cls(pollid = pollid, ip = ip, spam = spam)
            ballot.response = response
            ballot._commit()
        return ballot

def get_ballots(poll):
    return list(Ballot._query(Ballot.c._thing2_id == poll._id,
                              data = True))

def get_user_ballot(user, poll):
    return list(Ballot._query(Ballot.c._thing1_id == user._id,
                              Ballot.c._thing2_id == poll._id,
                              data = True))

