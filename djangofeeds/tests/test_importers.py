# -*- coding: utf-8 -*-
from __future__ import with_statement

import os
import time
import socket
import httplib as http
import tempfile
import unittest2 as unittest
import feedparser
import pytz
from datetime import datetime
from UserDict import UserDict
from contextlib import nested
from django.contrib.auth import authenticate

from djangofeeds.importers import FeedImporter
from djangofeeds.exceptions import FeedCriticalError
from djangofeeds.exceptions import TimeoutError, FeedNotFoundError
from djangofeeds import models
from djangofeeds.models import Feed, Post
from djangofeeds import feedutil

data_path = os.path.join(os.path.dirname(__file__), "data")

FEED_YIELDING_404 = "http://fr.yahoo.com/rssmhwqgiuyeqwgeqygqfyf"


def get_data_filename(name):
    return os.sep.join([data_path, name])


def get_data_file(name, mode="r"):
    with open(get_data_filename(name), mode) as file:
        return file.read()


class TestRegressionOPAL578(unittest.TestCase):

    def setUp(self):
        self.importer = FeedImporter()
        self.feeds = map(get_data_filename, ["t%d.xml" % i
                                              for i in reversed(range(1, 6))])

    def assertImportFeed(self, filename, name):
        importer = self.importer
        feed_obj = importer.import_feed(filename, local=True, force=True)
        self.assertEqual(feed_obj.name, name)
        return feed_obj

    def test_does_not_duplicate_posts(self):
        spool = tempfile.mktemp(suffix="ut", prefix="djangofeeds")

        def test_file(filename):
            try:
                with nested(open(filename), open(spool, "w")) as (r, w):
                    w.write(r.read())
                return self.assertImportFeed(spool,
                        "Saturday Morning Breakfast Cereal (updated daily)")
            finally:
                os.unlink(spool)

        for i in range(40):
            for filename in self.feeds:
                f = test_file(filename)

        posts = list(f.get_posts(limit=None))
        self.assertEqual(len(posts), 4)

        seen = set()
        for post in posts:
            self.assertNotIn(post.title, seen)
            seen.add(post.title)

        self.assertEqual(posts[0].title, "November 23, 2009")
        self.assertEqual(posts[1].title, "November 22, 2009")
        self.assertEqual(posts[2].title, "November 21, 2009")
        self.assertEqual(posts[3].title, "November 20, 2009")


class TestFeedImporter(unittest.TestCase):

    def setUp(self):
        self.feed = get_data_filename("example_feed.rss")
        self.empty_feed = get_data_filename("example_empty_feed.rss")
        self.feed_content_encoded = get_data_filename(
                                        "example_feed-content_encoded.rss")
        self.importer = FeedImporter()

    def test_import_feed_with_content_encoded_regr_OPAL552(self):
        """See https://bugs.opera.com/browse/OPAL-552"""
        # Change 29/11/10: removing <img because the new feedparser is
        # reordering the html
        feed = self.feed_content_encoded
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, u"La Bande Pas Dessinée")
        posts = feed_obj.post_set.order_by("-date_published")
        post_map = [
            (u"NEWS 4", None),
            (u"268 - Technique", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/268
"""),
                    (u"267 - Phénomène de Groupe", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/267
"""),
                    (u"266 - VDM", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/266
"""),
                    (u"265 - Inspecteur Sanchez : Encore Du Sang", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/265
"""),
                    (u"264 - Manque", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/264
"""),
                    (u"263 - Rosbeef", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/263
"""),
                    (u"262 - Geek Smic", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/262
"""),
                    (u"Résultats du Concours We Are The 90’s", u"""
étais un lèche-cul
"""),
                    (u"261 - Papy", """
src="http://www.labandepasdessinee.com/bpd/images/saison3/261
"""),
        ]
        for i, post in enumerate(posts):
            try:
                expects = post_map[i]
            except IndexError:
                expects = ("UNEXPECTED INDEX TITLE", "UNEXPECTED INDEX IMG")
            title, find_text = expects
            self.assertEqual(post.title, title)
            if find_text:
                self.assertTrue(post.content.find(find_text.strip()) != -1)

    def test_import_empty_feed(self):
        """Regression for OPAL-513"""
        feed = self.empty_feed
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, "(no title)")
        self.assertEqual(feed_obj.get_post_count(), 0, "feed has 0 items")
        self.assertEqual(feed_obj.feed_url, feed, "feed url is filename")

    def test_import_feed(self):
        feed = self.feed
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, "Lifehacker", "feed title is set")
        self.assertEqual(feed_obj.get_post_count(), 20, "feed has 20 items")
        self.assertEqual(feed_obj.feed_url, feed, "feed url is filename")
        self.assertTrue(feed_obj.description, "feed has description")

        posts = feed_obj.get_posts(limit=None)
        first_post = posts[0]
        self.assertEqual(first_post.guid, "Lifehacker-5147831")
        fmt = '%Y-%m-%d %H:%M:%S %Z%z'
        self.assertEqual(first_post.date_updated,
                datetime(2009, 02, 06, 04, 30, 0, 0,
                tzinfo=pytz.timezone('US/Pacific')).astimezone(
                    pytz.utc))

        for post in posts:
            self.assertTrue(post.guid, "post has GUID")
            self.assertTrue(post.title, "post has title")
            if hasattr(post, "enclosures"):
                self.assertEqual(post.enclosures.count(), 0,
                    "post has no enclosures")
            self.assertTrue(post.link, "post has link")
            self.assertTrue(post.content)

        feed_obj2 = importer.import_feed(feed)
        self.assertTrue(feed_obj2.date_last_refresh,
                        "Refresh date set")
        self.assertEqual(feed_obj2.id, feed_obj.id,
                        "Importing same feed doesn't create new object")
        self.assertEqual(feed_obj2.get_post_count(), 20,
                        "Re-importing feed doesn't give duplicates")

    def test_404_feed_raises_ok(self):
        importer = self.importer
        with self.assertRaises(FeedNotFoundError):
            importer.import_feed(FEED_YIELDING_404)

    def test_missing_date_feed(self):
        """Try to reproduce the constant date update bug."""
        feed = get_data_filename("buggy_dates.rss")
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        last_post = feed_obj.get_posts()[0]

        time.sleep(1)

        feed2 = get_data_filename("buggy_dates.rss")
        feed_obj2 = importer.import_feed(feed2, local=True)
        last_post2 = feed_obj2.get_posts()[0]

        # if the post is updated, we should see a different datetime
        self.assertEqual(last_post.date_updated, last_post2.date_updated)

    def test_missing_date_and_guid_feed(self):
        """Try to reproduce the constant date update bug."""
        feed = get_data_filename("buggy_dates_and_guid.rss")
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        last_post = feed_obj.get_posts()[0]

        time.sleep(1)

        feed2 = get_data_filename("buggy_dates_and_guid.rss")
        feed_obj2 = importer.import_feed(feed2, local=True)
        last_post2 = feed_obj2.get_posts()[0]

        # if the post is updated, we should see a different datetime
        self.assertEqual(last_post.date_updated, last_post2.date_updated)

    def test_socket_timeout(self):

        class _TimeoutFeedImporter(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                raise socket.timeout(1)

        feed2 = "foofoobar.rss"
        with self.assertRaises(TimeoutError):
                _TimeoutFeedImporter().import_feed(feed2, local=True)
        self.assertTrue(Feed.objects.get(feed_url=feed2))

    def test_update_feed_socket_timeout(self):

        class _TimeoutFeedImporter(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                raise socket.timeout(1)

        Feed.objects.all().delete()
        importer = FeedImporter(update_on_import=False)
        feed_obj = importer.import_feed(self.feed, local=True, force=True)

        simporter = _TimeoutFeedImporter()
        feed_obj = simporter.update_feed(feed_obj=feed_obj, force=True)
        self.assertEqual(feed_obj.last_error, models.FEED_TIMEDOUT_ERROR)

    def test_update_feed_parse_feed_raises(self):

        class _RaisingFeedImporter(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                raise KeyError("foo")

        Feed.objects.all().delete()
        importer = FeedImporter(update_on_import=False)
        feed_obj = importer.import_feed(self.feed, local=True, force=True)

        simporter = _RaisingFeedImporter()
        feed_obj = simporter.update_feed(feed_obj=feed_obj, force=True)
        self.assertEqual(feed_obj.last_error, models.FEED_GENERIC_ERROR)

    def test_update_feed_not_modified(self):

        class _Verify(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                feed = super(_Verify, self).parse_feed(*args, **kwargs)
                feed["status"] = http.NOT_MODIFIED
                return feed

        Feed.objects.all().delete()
        importer = FeedImporter(update_on_import=False)
        feed_obj = importer.import_feed(self.feed, local=True, force=True)
        self.assertTrue(_Verify().update_feed(feed_obj=feed_obj, force=False))

    def test_update_feed_error_status(self):

        class _Verify(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                return {"status": http.NOT_FOUND}

        Feed.objects.all().delete()
        importer = FeedImporter(update_on_import=False)
        feed_obj = importer.import_feed(self.feed, local=True, force=True)

        feed_obj = _Verify().update_feed(feed_obj=feed_obj, force=True)
        self.assertEqual(feed_obj.last_error, models.FEED_NOT_FOUND_ERROR)

    def test_parse_feed_raises(self):

        class _RaisingFeedImporter(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                raise KeyError("foo")

        feed2 = "foo1foo2bar3.rss"
        with self.assertRaises(FeedCriticalError):
                _RaisingFeedImporter().import_feed(feed2, local=True)
        with self.assertRaises(Feed.DoesNotExist):
            Feed.objects.get(feed_url=feed2)

    def test_http_modified(self):
        now = time.localtime()
        now_as_dt = datetime.fromtimestamp(time.mktime(
            now)).replace(tzinfo=pytz.utc)

        class _Verify(FeedImporter):

            def parse_feed(self, *args, **kwargs):
                feed = super(_Verify, self).parse_feed(*args, **kwargs)
                feed.modified = now
                return feed

        i = _Verify()
        feed = i.import_feed(self.feed, local=True, force=True)
        self.assertEqual(feed.http_last_modified, now_as_dt)

    def test_http_redirects(self):

        class MockFeed(UserDict):

            def __init__(self, status, href):
                self.href = href
                self.data = {"status": status}

        class _Verify(FeedImporter):

            def __init__(self, *args, **kwargs):
                self.redirect_to = kwargs.pop("redirect_to", None)
                super(_Verify, self).__init__(*args, **kwargs)

            def import_feed(self, feed_url, local=False, force=False):
                if not local:
                    return feed_url
                return super(_Verify, self).import_feed(feed_url,
                                                        local=local,
                                                        force=force)

            def parse_feed(self, feed_url):
                return MockFeed(http.FOUND, self.redirect_to)

        i1 = _Verify(redirect_to="http://redirect.ed/")
        href = i1.import_feed("xxxyyyzzz", local=True)
        self.assertEqual(href, "http://redirect.ed/")

        i2 = _Verify(redirect_to="xxxyyyzzz")
        with self.assertRaises(AttributeError):
            i2.import_feed("xxxyyyzzz", local=True)

    def test_import_categories(self):
        if not Feed.supports_categories:
            return
        Feed.objects.all().delete()
        importer = FeedImporter(include_categories=True)
        feed = importer.import_feed(self.feed, local=True, force=True)
        post = feed.post_set.order_by("-date_published")[0]
        categories = [cat.name for cat in post.categories.all()]
        for should in ("Downloads", "Screenshots", "Skins", "Themes"):
            self.assertIn(should, categories)

        self.assertEqual(len(categories), 13)

    def test_update_on_import(self):

        class _Verify(FeedImporter):
            updated = False

            def update_feed(self, *args, **kwargs):
                self.updated = True

        imp1 = _Verify(update_on_import=False)
        imp1.import_feed(self.feed, local=True, force=True)
        self.assertFalse(imp1.updated)

        imp2 = _Verify(update_on_import=True)
        imp1.import_feed(self.feed, local=True, force=True)
        self.assertFalse(imp2.updated)

    def test_generate_utf8_encode_guid_bug(self):
        """Some feeds trigger utf8 bugs when the guid is generated."""
        feed_str = get_data_file("mobile_it.rss")
        feed = feedparser.parse(feed_str)
        for entry in feed["entries"]:
            guid = feedutil.get_entry_guid(feed, entry)
            self.assertTrue(guid.startswith("http://"))

        feed_str = get_data_file("no-steam.rss")
        feed = feedparser.parse(feed_str)
        for entry in feed["entries"]:
            guid = feedutil.get_entry_guid(feed, entry)
            self.assertTrue(guid)

        feed_str = get_data_file("fakultet.xml")
        feed = feedparser.parse(feed_str)
        for entry in feed["entries"]:
            guid = feedutil.get_entry_guid(feed, entry)
            self.assertTrue(guid)

        feed_str = get_data_file("poker_pl.rss")
        feed = feedparser.parse(feed_str)
        for entry in feed["entries"]:
            guid = feedutil.get_entry_guid(feed, entry)
            self.assertTrue(guid)

    def test_generate_utf8_encode_guid_bug_time_mk(self):
        feed_str = get_data_file("time_mk.rss")
        feed = feedparser.parse(feed_str)
        self.assertTrue(len(feed["entries"]) > 0)
        for entry in feed["entries"]:
            guid = feedutil.get_entry_guid(feed, entry)
            self.assertTrue(guid)

        imported_feed = self.importer.import_feed(feed_str, local=True,
                                                            force=True)
        self.assertTrue(imported_feed.post_set.count() > 0)
        for post in imported_feed.post_set.all():
            guid = post.guid
            self.assertTrue(guid)

    def test_entry_limit(self):
        feed = self.feed
        importer = FeedImporter(post_limit=10)
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, "Lifehacker", "feed title is set")
        self.assertEqual(feed_obj.get_post_count(), 10, "feed has 10 items")

    def test_double_post_bug(self):
        """With some feeds, the posts seem to be imported several times."""
        feed_str = get_data_file("lefigaro.rss")
        imported_feed = self.importer.import_feed(feed_str, local=True,
                                                            force=True)
        post_count = imported_feed.post_set.count()
        imported_feed = self.importer.import_feed(feed_str, local=True,
                                                            force=True)
        self.assertEqual(imported_feed.post_set.count(), post_count,
            "Posts seems to be imported twice.")
