import unittest
from datetime import datetime

from djangofeeds import feedutil
from djangofeeds.feedutil import date_to_datetime, find_post_content


class TestDateToDatetime(unittest.TestCase):

    def test_no_date(self):
        x = date_to_datetime("date_test")
        date = x(None, {})
        now = datetime.now()
        self.assertEquals((date.year, date.month, date.day),
                          (now.year, now.month, now.day))

    def test_wrong_type(self):
        x = date_to_datetime("date_test")
        date = x(None, {"date_test": object()})
        now = datetime.now()
        self.assertEquals((date.year, date.month, date.day),
                          (now.year, now.month, now.day))


class TestFindPostContent(unittest.TestCase):

    def test_returns_empty_string_on_UnicodeDecodeError(self):

        def raise_UnicodeDecodeError(*args, **kwargs):
            return "quickbrown".encode("zlib").encode("utf-8")

        prev = feedutil.truncate_html_words
        feedutil.truncate_html_words = raise_UnicodeDecodeError
        try:
            self.assertEquals(find_post_content(None, {
                                    "description": "foobarbaz"}), "")
        finally:
            feedutil.truncate_html_words = prev
