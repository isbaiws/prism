from __future__ import absolute_import
from unittest import TestCase

from mongoengine import Document, StringField, Q, InvalidQueryError

class Email(Document):
    from_ = StringField()

class KeySplitTestCase(TestCase):
    def test_key_split_at_right_position(self):
        """See https://github.com/MongoEngine/mongoengine/pull/619"""
        try:
            Q(from___contains='qq').to_query(Email)
        except InvalidQueryError:
            self.fail("A bug in mongoengine, try install https://github.com/dhudaddy/mongoengine")

