import os
import unittest
from djangofeeds.utils import naturaldate
from datetime import datetime, timedelta


class TestNaturalDate(unittest.TestCase):

    def test_in_the_future(self):
        then = datetime.now() + timedelta(seconds=1)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(minutes=30)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(hours=30)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(days=2)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(days=8)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(days=5 * 7)
        self.assertEquals(naturaldate(then), "just now")
        then = datetime.now() + timedelta(days=413)
        self.assertEquals(naturaldate(then), "just now")

    def test_just_now(self):
        now = datetime.now()
        self.assertEquals(naturaldate(now), "just now")

    def test_seconds_ago(self):
        for n in xrange(0, 59 + 1):
            n_seconds_ago = datetime.now() - timedelta(seconds=n)
            self.assertEquals(naturaldate(n_seconds_ago),
                "just now")

    def test_one_minute_ago(self):
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self.assertEquals(naturaldate(one_minute_ago),
                "1 minute ago")

    def test_minutes_ago(self):
        for n in xrange(2, 59 + 1):
            n_minutes_ago = datetime.now() - timedelta(minutes=n)
            self.assertEquals(naturaldate(n_minutes_ago),
                "%d minutes ago" % n)

    def test_one_hour_ago(self):
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.assertEquals(naturaldate(one_hour_ago), "1 hour ago")

    def test_hours_ago(self):
        for n in xrange(2, 24):
            n_hours_ago = datetime.now() - timedelta(hours=n)
            self.assertEquals(naturaldate(n_hours_ago),
                "%d hours ago" % n)
        yesterday = datetime.now() - timedelta(hours=24)
        self.assertEquals(naturaldate(yesterday),
                "yesterday at %s" % yesterday.strftime("%H:%M"))

    def test_yesterday(self):
        yesterday = datetime.now() - timedelta(days=1)
        self.assertEquals(naturaldate(yesterday),
                "yesterday at %s" % yesterday.strftime("%H:%M"))

    def test_days_ago(self):
        yesteryesterday = datetime.now() - timedelta(days=2)
        self.assertEquals(naturaldate(yesteryesterday),
                "2 days ago")

    def test_one_week_ago(self):
        one_week_ago = datetime.now() - timedelta(days=7)
        self.assertEquals(naturaldate(one_week_ago),
                "1 week ago")

    def test_weeks_ago(self):
        for n in xrange(2, 5):
            n_weeks_ago = datetime.now() - timedelta(days=n * 7)
            self.assertEquals(naturaldate(n_weeks_ago),
                "%d weeks ago" % n)

    def test_one_month_ago(self):
        one_month_ago = datetime.now() - timedelta(days=30)
        self.assertEquals(naturaldate(one_month_ago),
                "1 month ago")

    def test_months_ago(self):
        for n in xrange(2, 13):
            n_months_ago = datetime.now() - timedelta(days=n * 30)
            self.assertEquals(naturaldate(n_months_ago),
                "%d months ago" % n)

    def test_one_year_ago(self):
        one_year_ago = datetime.now() - timedelta(days=365)
        self.assertEquals(naturaldate(one_year_ago),
                "1 year ago")

    def test_years_ago(self):
        for n in xrange(2, 30):
            n_years_ago = datetime.now() - timedelta(days=n * 365)
            self.assertEquals(naturaldate(n_years_ago),
                "%d years ago" % n)
