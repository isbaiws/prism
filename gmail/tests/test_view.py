# coding: utf-8
import re
from unittest import skip
from django.test import TestCase
from django.core.urlresolvers import reverse, NoReverseMatch

from gmail import views

class NoDBTestCase(TestCase):
    def _fixture_setup(self):
        pass

    def _fixture_teardown(self):
        pass

class ViewTestCase(NoDBTestCase):
    def _test_404(self, view_name):
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse(view_name, args=('123',)))
        resp = self.client.get(reverse(view_name, args=('111111111111111111111111',)))
        self.assertEqual(resp.status_code, 404)

    def test_email_detail_404(self):
        self._test_404('email_detail')

    def test_resource_404(self):
        self._test_404('resource')

    @skip('Skipped until I find a way to fake the content')
    def test_post_more_than_50m_data(self):
        self.client.post(reverse('email_list'), {'a':1}, CONTENT_LENGTH=str(50*1024*1024))

    def test_deletion(self):
        # Add one
        resp = self.client.post(reverse('email_list'), 'placeholder', content_type='text/plain')

        id_matt = re.search(r'\w{24}', resp.content)
        self.assertIsNotNone(id_matt)
        id_str = id_matt.group()
        # Delete one
        resp = self.client.get(reverse('delete_email', args=(id_str,)))
        self.assertEqual(resp.status_code, 302)

        # Not found
        resp = self.client.get(reverse('email_detail', args=(id_str,)))
        self.assertEqual(resp.status_code, 404)
        # Maybe should test whether resources get deleted or not

        # What about delete again?
        resp = self.client.get(reverse('delete_email', args=(id_str,)))
        self.assertEqual(resp.status_code, 302)

