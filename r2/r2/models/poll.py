import re
from pylons import c, g, request
from r2.lib.db.thing import Thing, Relation, NotFound, MultiRelation, CreationError
from account import Account
from r2.lib.utils import to36

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
	show_results = user_has_voted(commentid, c.user)
	pollids = []
	def checkmatch(match):
		pollid = match.group(1)
		pollids.append(pollid)
		return renderpoll(pollid, commentid, show_results)
	
	rendered_body = re.sub(pollid_re, checkmatch, text)
	if(len(pollids) > 0):
		return rendered_body + pollfooter(commentid)
	else:
		return rendered_body

def user_has_voted(comment, user):
	# TODO
	return false

def pollfooter(commentid):
	return "<input type=\"button\" value=\"Submit\"/> <input type=\"button\" value=\"Reveal\"/>"

def createpoll(commentid, polltype, args):
	poll = Poll.createpoll(commentid, args[0], args[1:])
	return poll._id

def renderpoll(pollid, commentid, show_results):
	try:
		poll = Poll._byID(pollid)
		if(show_results):
			return poll.render_results()
		else:
			return poll.render()
	except NotFound:
		return "Error: Poll not found!"

class Poll(Thing):
	@classmethod
	def createpoll(cls, commentid, description, options):
		poll = cls(commentid = commentid,
		           description = description,
		           choices = options)
		poll._commit()
		return poll
	
	def render(self):
		ret = "<form><B>" + self.description + "\n"
		for ii in range(len(self.choices)):
			ret += "<input type=\"radio\" name=\"" + to36(self.commentid) + "_" + self._id36 + "\" value=\"" + str(ii) + "\">" + self.choices[ii] + "</input>"
		ret += "</B></form>"
		return ret
	
	def render_results(self):
		# TODO
		return "Poll Results"

class Ballot(Relation(Account, Poll)):
	# TODO
	@classmethod
	def submitballot(cls, pollid, response):
		ballot = cls(pollid = pollid,
		             response = response)
		ballot._commit()
		return ballot

