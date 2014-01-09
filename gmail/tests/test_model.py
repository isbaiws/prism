# coding: utf-8
import ipdb
from unittest import TestCase
import os.path

from mongoengine import GridFSProxy
from gmail import models

class DeleteTestCase(TestCase):
    def setUp(self):
        fpath = os.path.join(os.path.dirname(__file__), 'fixtures/pic.eml')
        # Add one
        with open(fpath) as fp:
            self.e = models.Email.from_fp(fp)
        self.e.save()

    def test_delete_resources(self):
        self.assertRegexpMatches(str(self.e.id), r'^\w{24}$')
        self.assertIsInstance(models.Email.objects(id=self.e.id).first(),
                models.Email)

        resources = self.e.resources or []
        self.assertNotEqual(resources, [])
        resources.extend(self.e.attachments or [])
        # All exist
        for resc in self.e.resources:
            self.assertIsNotNone(GridFSProxy().get(resc.grid_id))

        self.e.delete()
        # None exsits
        self.assertIsNone(models.Email.objects(id=self.e.id).first())
        for resc in self.e.resources:
            self.assertIsNone(GridFSProxy().get(resc.grid_id))

    def tearDown(self):
        self.e.delete()

