# coding: utf-8
from unittest import TestCase
from cStringIO import StringIO

from gmail import models

class ModelTestCase(TestCase):
    def test_decode_rfc2047(self):
        res = models.decode_rfc2047('=?GBK?B?16q8xKO616q8xKO6MTE5z/u3wMjVu+62r82o1qo=?=')
        self.assertIsInstance(res, unicode)
        self.assertEqual(res, u'转寄：转寄：119消防日活动通知')

    def test_decode_rfc2047_with_broken_line(self):
        u = models.decode_rfc2047('=?GB2312?B?ob7Jz7qj1b6hv9PDVmlzdWFsIFN0dWRpbyC/qreiaU9TvLBhbmRyb2lk06bTw6OsxOPSsr/J0tSj\
    oQ==?=')
        self.assertEqual(u, u'【上海站】用Visual Studio 开发iOS及android应用，你也可以！')

    def test_defective_email(self):
        pass
        # models.Email.from_fp(StringIO(defective_email))

