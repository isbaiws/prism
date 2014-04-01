#coding: utf-8
import logging
import ipdb

from django.contrib.auth import hashers
from mongoengine import (
        Document, StringField, BooleanField, ListField, UUIDField, ReferenceField
    )
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)
    is_superuser = BooleanField(default=False)
    device_ids = ListField(UUIDField(binary=True), default=list)
    groups = ListField(ReferenceField('Group'))

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['username', 'password']
    meta = {
        # There will be a '_cls' field in db, if allow inheritance
        'allow_inheritance': False,
        'indexes': ['username', 'device_ids'],
    }

    def get_username(self):
        "Return the identifying username for this User"
        return self.username

    def __unicode__(self):
        return self.get_username()

    def natural_key(self):
        return (self.get_username(),)

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def is_active(self):
        return True

    def set_password(self, raw_password):
        self.password = hashers.make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return hashers.check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = hashers.make_password(None)

    def has_usable_password(self):
        return hashers.is_password_usable(self.password)

    @classmethod
    def create_user(cls, username, password, is_superuser=False, groups=[]):
        user = cls(username=username, is_superuser=is_superuser, groups=groups)
        user.set_password(password)
        user.save()
        return user

    def delete(self):
        # In case of circular import
        from .email import Email
        # Remove all emails belonging to me
        for e in Email.objects(owner=self.id):
            e.delete()
        from .group import Group
        Group.objects.update(pull__managers=self.id)
        super(User, self).delete()

    def groups_in_charge(self):
        from .group import Group
        return Group.objects(managers=self.id)

    def set_groups(self, groups):
        def get_gid(g):
            if isinstance(g, Document):
                return g.id
            return ObjectId(g)
        already_in = set(g.id for g in self.groups)
        new_coming = set(map(get_gid, groups))

        for g in new_coming-already_in:  # New ones
            self.update(add_to_set__groups=g)

        for g in already_in-new_coming:  # Deleted ones
            self.update(pull__groups=g)
            from .group import Group
            if self in Group.get_by_id(g).managers:
                Group.get_by_id(g).update(pull__managers=self.id)

    @classmethod
    def exist(cls, **kwargs):
        return cls.objects(**kwargs).first()

    @classmethod
    def get_by_id(cls, uid):
        if not uid:  # None is a valid objectid?
            return False
        if ObjectId.is_valid(uid):
            return cls.objects(id=uid).first()
        return False
