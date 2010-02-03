import unittest
from datetime import timedelta

from djangofeeds import conf


class TestConf(unittest.TestCase):

    def test_interval(self):
        self.assertEquals(conf._interval(timedelta(seconds=10)),
                          timedelta(seconds=10))
        self.assertEquals(conf._interval(30), timedelta(seconds=30))
