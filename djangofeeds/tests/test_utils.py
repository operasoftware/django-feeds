import pytz
import unittest2 as unittest
from datetime import datetime, timedelta

from djangofeeds.utils import naturaldate
from djangofeeds.feedutil import (entries_by_date,
                                  get_entry_guid,
                                  date_to_datetime)


class TestNaturalDate(unittest.TestCase):

    def test_empty_date(self):
        self.assertEqual(naturaldate(None), "")

    def test_in_the_future(self):
        then = datetime.now(pytz.utc) + timedelta(seconds=1)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(minutes=30)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(hours=30)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(days=2)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(days=8)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(days=5 * 7)
        self.assertEqual(naturaldate(then), "just now")
        then = datetime.now(pytz.utc) + timedelta(days=413)
        self.assertEqual(naturaldate(then), "just now")

    def test_just_utcnow(self):
        now = datetime.now(pytz.utc)
        self.assertEqual(naturaldate(now), "just now")

    def test_seconds_ago(self):
        for n in xrange(0, 59 + 1):
            n_seconds_ago = datetime.now(pytz.utc) - timedelta(seconds=n)
            self.assertEqual(naturaldate(n_seconds_ago), "just now")

    def test_one_minute_ago(self):
        one_minute_ago = datetime.now(pytz.utc) - timedelta(minutes=1)
        self.assertEqual(naturaldate(one_minute_ago), "1 minute ago")

    def test_minutes_ago(self):
        for n in xrange(2, 59 + 1):
            n_minutes_ago = datetime.now(pytz.utc) - timedelta(minutes=n)
            self.assertEqual(naturaldate(n_minutes_ago),
                              "%d minutes ago" % n)

    def test_one_hour_ago(self):
        one_hour_ago = datetime.now(pytz.utc) - timedelta(hours=1)
        self.assertEqual(naturaldate(one_hour_ago), "1 hour ago")

    def test_hours_ago(self):
        for n in xrange(2, 24):
            n_hours_ago = datetime.now(pytz.utc) - timedelta(hours=n)
            self.assertEqual(naturaldate(n_hours_ago),
                "%d hours ago" % n)
        yesterday = datetime.now(pytz.utc) - timedelta(hours=24)
        self.assertEqual(naturaldate(yesterday),
                "yesterday at %s" % yesterday.strftime("%H:%M"))

    def test_yesterday(self):
        yesterday = datetime.now(pytz.utc) - timedelta(days=1)
        self.assertEqual(naturaldate(yesterday),
                "yesterday at %s" % yesterday.strftime("%H:%M"))

    def test_days_ago(self):
        yesteryesterday = datetime.now(pytz.utc) - timedelta(days=2)
        self.assertEqual(naturaldate(yesteryesterday), "2 days ago")

    def test_one_week_ago(self):
        one_week_ago = datetime.now(pytz.utc) - timedelta(days=7)
        self.assertEqual(naturaldate(one_week_ago), "1 week ago")

    def test_weeks_ago(self):
        for n in xrange(2, 5):
            n_weeks_ago = datetime.now(pytz.utc) - timedelta(days=n * 7)
            self.assertEqual(naturaldate(n_weeks_ago), "%d weeks ago" % n)

    def test_one_month_ago(self):
        one_month_ago = datetime.now(pytz.utc) - timedelta(days=30)
        self.assertEqual(naturaldate(one_month_ago), "1 month ago")

    def test_months_ago(self):
        for n in xrange(2, 13):
            n_months_ago = datetime.now(pytz.utc) - timedelta(days=n * 30)
            self.assertEqual(naturaldate(n_months_ago), "%d months ago" % n)

    def test_one_year_ago(self):
        one_year_ago = datetime.now(pytz.utc) - timedelta(days=365)
        self.assertEqual(naturaldate(one_year_ago), "1 year ago")

    def test_years_ago(self):
        for n in xrange(2, 30):
            n_years_ago = datetime.now(pytz.utc) - timedelta(days=n * 365)
            self.assertEqual(naturaldate(n_years_ago),
                "%d years ago" % n)

    def test_entries_by_date(self):
        now = datetime.now(pytz.utc)
        proper_list = [
            {"title": "proper 1", "date_parsed": now},
            {"title": "proper 2",
             "date_parsed": now - timedelta(seconds=10)},
            {"title": "proper 3",
             "date_parsed": now - timedelta(seconds=20)},
            {"title": "proper 4",
             "date_parsed": now - timedelta(seconds=30)},
        ]
        self.assertEqual(proper_list, entries_by_date(proper_list))

        improper_list = [
            {"title": "improper 1"},
            {"title": "improper 2"},
            {"title": "improper 3"},
            {"title": "improper 4"},
        ]

        self.assertEqual(improper_list, entries_by_date(improper_list))

    def test_missing_guid(self):
        entries = [
            {"title": u"first",
             "link": u"toto"},
            {"title": u"first",
             "link": u"tata"},
        ]
        self.assertTrue(len(get_entry_guid(None, entries[0])) > 0)
        self.assertNotEqual(get_entry_guid(None, entries[0]),
                            get_entry_guid(None, entries[1]))

    def test_faulty_dates2(self):
        entries = [
            {"title": u"first",
             "updated": u"06/01/2010 CET",
             "updated_parsed": None},
            {"title": u"second",
             "updated": u"23/12/2009 CET",
             "updated_parsed": None},
        ]
        entries = entries_by_date(entries)
        d1 = date_to_datetime("published_parsed")(None, entries[0])
        d2 = date_to_datetime("published_parsed")(None, entries[1])
        self.assertTrue(d1 > d2)

        self.assertEqual(entries, entries_by_date(entries))
        reversed_entries = list(entries)
        reversed_entries.reverse()
        self.assertNotEqual(entries, reversed_entries)
        self.assertEqual(entries, entries_by_date(reversed_entries))
