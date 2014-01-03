#coding: utf-8
from unittest import TestCase

from gmail import attachreader

class AttachReaderTestCase(TestCase):
    def test_txt_reader(self):
        res = attachreader.read('我的', 'a.txt')
        self.assertIsInstance(res, unicode)
        self.assertEqual(res, u'我的')
