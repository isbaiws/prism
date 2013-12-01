"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from mimeparser import from_fp
import os.path


# class SimpleTest(TestCase):
#     def test_basic_addition(self):
#         """
#         Tests that 1 + 1 always equals 2.
#         """
#         self.assertEqual(1 + 1, 2)
dirname = os.path.dirname(__file__)
fn = os.path.join(dirname, 'fixtures/multipart_alternative.eml')
e = from_fp(open(fn))
e.save()
