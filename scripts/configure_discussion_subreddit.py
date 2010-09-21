#!/usr/bin/python

def configure_discussion():
  from r2.models import Subreddit
  s = Subreddit._by_name('discussion')
  s.header_image = "/static/logo-discussion.png"
  s.stylesheet = "/static/discussion.css"
  s.infotext = u"""This part of the site is for the discussion of topics not
                   yet ready or not suitable for normal top-level posts.
                   Votes are only worth \N{PLUS-MINUS SIGN}1 point here. For
                   more info, see [about Less Wrong](/about)."""
  s._commit()

