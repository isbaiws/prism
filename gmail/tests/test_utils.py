#coding: utf-8
from __future__ import absolute_import
from unittest import TestCase

from gmail import utils
#
# class DjangoTestCase(TestCase):
#     def test_long_header(self):
#         """A django bug, which hasn't been fixed, see #20889'"""
#         h = HttpResponse()
#         f = '\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91\xe6\x88\x91'.decode('utf-8')
#         h['Content-Disposition'] = u'attachment; filename="%s"' % f

class UtilsTestCase(TestCase):

    def test_building_content_disposition(self):
        filename = u"中文  .txt"
        self.assertEqual(utils.build_content_disposition(filename),
                u"""attachment; filename="%E4%B8%AD%E6%96%87%20%20.txt"; filename*=utf-8''%E4%B8%AD%E6%96%87%20%20.txt""")
        filename = u"中文  .txt".encode('utf-8')
        self.assertEqual(utils.build_content_disposition(filename),
                                u"""attachment; filename="%E4%B8%AD%E6%96%87%20%20.txt"; filename*=utf-8''%E4%B8%AD%E6%96%87%20%20.txt""")

        filename = u"ss\rrr\nnn\n\r\r\n"
        self.assertEqual(utils.build_content_disposition(filename), u'''attachment; filename="ssrrnn"; filename*=utf-8''ssrrnn''')
