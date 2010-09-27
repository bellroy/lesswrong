#!/usr/bin/python

def configure_discussion():
  from r2.models import Subreddit
  s = Subreddit._by_name('discussion')
  s.header = "/static/logo-discussion.png"
  s.stylesheet = "/static/discussion.css"
  s.infotext = u"""This part of the site is for the discussion of topics not
                   yet ready or not suitable for normal top-level posts.
                   Votes are only worth \N{PLUS-MINUS SIGN}1 point here. For
                   more information, see [About Less Wrong](/about-less-wrong)."""

  s.posts_per_page_multiplier = 4
  s.post_karma_multiplier = 1
  s._commit()

