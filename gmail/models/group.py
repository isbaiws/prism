#coding: utf-8
from __future__ import absolute_import
import ipdb
import logging
from bson.objectid import ObjectId

from mongoengine import (
        Document, StringField, ListField, ReferenceField
    )

logger = logging.getLogger(__name__)

class Group(Document):
    name = StringField(required=True, unique=True)
    # Lazy dereference to avoid circular import
    managers = ListField(ReferenceField('User'))

    meta = {
        'indexes': ['name',],
    }

    def __unicode__(self):
        return self.name

    # Django will take care of the conversion
    # def __str__(self):
    #     pass

    def members(self):
        from .user import User
        return User.objects(groups=self.id)

    @classmethod
    def get_by_id(cls, gid):
        if not gid:  # None is a valid objectid?
            return False
        if ObjectId.is_valid(gid):
            return cls.objects(id=gid).first()
        return False
