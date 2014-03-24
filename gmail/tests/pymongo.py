from unittest import TestCase
from bson import BSON

class PymongoTestCase(TestCase):

    def test_installing_the_right_pymongo(self):
        try:
            BSON(BSON.encode({'a':1})).decode()
        except TypeError:
            self.fail('You have installed a wrong pymongo, try pip install pymongo again')
