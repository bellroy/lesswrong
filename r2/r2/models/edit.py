from r2.lib.db.thing import Thing
from account import Account
from link import Link

import difflib

class Edit(Thing):
    """Used to track edits on Link"""

    @classmethod
    def _new(cls, link, user, new_content):
        return Edit(link_id = link._id,
                    author_id = user._id,
                    diff = Edit.create_diff(link.article, new_content))

    @staticmethod
    def create_diff(old_content, new_content):
        return list(difflib.unified_diff(old_content.splitlines(), new_content.splitlines()))

    @classmethod
    def add_props(cls, user, wrapped):
        for item in wrapped:
            item.permalink = item.link.make_permalink_slow()

    @staticmethod
    def cache_key(wrapped):
        return False

    def keep_item(self, wrapped):
        return True

    @property
    def link(self):
        return Link._byID(self.link_id, data=True)

    @property
    def link_author(self):
        return Account._byID(self.link.author_id, data=True)

    diff_marker_to_class = {
        "+" : "new",
        "-" : "del",
        "@" : "context"
    }

    @staticmethod
    def diff_line_style(line):
        """Used in the template to find the css class for each diff line"""
        if len(line)<=0: return ""
        return Edit.diff_marker_to_class.get(line[0],"")

