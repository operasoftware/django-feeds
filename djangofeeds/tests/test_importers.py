# -*- coding: utf-8 -*-
from __future__ import with_statement

import os
import sys
import tempfile
import unittest
from contextlib import nested

from django.contrib.auth import authenticate

from yadayada.test.user import create_random_user

from djangofeeds.importers import FeedImporter
from djangofeeds.exceptions import FeedCriticalError
from djangofeeds.exceptions import TimeoutError, FeedNotFoundError
from djangofeeds.models import Feed, Post, Enclosure

data_path = os.path.join(os.path.dirname(__file__), 'data')

FEED_YIELDING_404 = "http://www.yahoo.fr/rssmhwqgiuyeqwgeqygqfyf"


def get_data_filename(name):
    return os.sep.join([data_path, name])


def get_data_file(name, mode="r"):
    with open(get_data_filename(name), mode) as file:
        return file.read()


class TestRegressionOPAL578(unittest.TestCase):

    def setUp(self):
        self.importer = FeedImporter()
        self.feeds = map(get_data_filename, ["t%d.xml" % i
                                                for i in range(1, 10)])

    def assertImportFeed(self, filename, name):
        importer = self.importer
        feed_obj = importer.import_feed(filename, local=True, force=True)
        self.assertEqual(feed_obj.name, name)
        return feed_obj

    def test_does_not_duplicate_posts(self):
        spool = tempfile.mktemp(suffix="ut", prefix="djangofeeds")
        for i in range(20):
            for filename in self.feeds:
                with nested(open(filename), open(spool, "w")) as (r, w):
                    w.write(r.read())
                    f = self.assertImportFeed(spool, "Monsieur Le Chien")
        self.assertEqual(f.post_set.all().count(), 10)


class TestFeedImporter(unittest.TestCase):

    def setUp(self):
        randuser = create_random_user()
        self.user = authenticate(username=randuser.username,
                                 password=randuser.username)
        self.assertEqual(randuser.username, self.user.username)
        self.assertTrue(self.user.is_authenticated(),
                        "Random user created successfully")
        self.feed = get_data_filename("example_feed.rss")
        self.empty_feed = get_data_filename("example_empty_feed.rss")
        self.feed_content_encoded = get_data_filename(
                                        "example_feed-content_encoded.rss")
        self.importer = FeedImporter()

    def test_import_feed_with_content_encoded_regr_OPAL552(self):
        """See https://bugs.opera.com/browse/OPAL-552"""
        feed = self.feed_content_encoded
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, u"La Bande Pas Dessinée")
        posts = feed_obj.post_set.all()
        post_map = [
            (u"NEWS 4", None),
            (u"268 - Technique", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/268
"""),
                    (u"267 - Phénomène de Groupe", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/267
"""),
                    (u"266 - VDM", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/266
"""),
                    (u"265 - Inspecteur Sanchez : Encore Du Sang", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/265
"""),
                    (u"264 - Manque", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/264
"""),
                    (u"263 - Rosbeef", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/263
"""),
                    (u"262 - Geek Smic", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/262
"""),
                    (u"Résultats du Concours We Are The 90’s", u"""
étais un lèche-cul
"""),
                    (u"261 - Papy", """
<img src="http://www.labandepasdessinee.com/bpd/images/saison3/261
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
        self.assertEqual(feed_obj.post_set.count(), 0, "feed has 0 items")
        self.assertEqual(feed_obj.feed_url, feed, "feed url is filename")

    def test_import_feed(self):
        feed = self.feed
        importer = self.importer
        feed_obj = importer.import_feed(feed, local=True)
        self.assertEqual(feed_obj.name, "Lifehacker", "feed title is set")
        self.assertEqual(feed_obj.post_set.count(), 20, "feed has 20 items")
        self.assertEqual(feed_obj.feed_url, feed, "feed url is filename")
        self.assertTrue(feed_obj.description, "feed has description")

        posts = feed_obj.post_set.all()
        first_post = posts[0]
        self.assertEquals(first_post.guid, "Lifehacker-5147831")
        self.assertEquals(str(first_post.date_updated), "2009-02-06 12:30:00")
        for post in posts:
            self.assertTrue(post.guid, "post has GUID")
            self.assertTrue(post.title, "post has title")
            self.assertEquals(post.enclosures.count(), 0,
                "post has no enclosures")
            #self.assertTrue(len(post.author), "post has author")
            self.assertTrue(post.link, "post has link")
            self.assertTrue(post.content)

        feed_obj2 = importer.import_feed(feed)
        self.assertTrue(feed_obj2.date_last_refresh,
                        "Refresh date set")
        self.assertEqual(feed_obj2.id, feed_obj.id,
                        "Importing same feed doesn't create new object")
        self.assertEqual(feed_obj2.post_set.count(), 20,
                        "Re-importing feed doesn't give duplicates")

    def test_404_feed_raises_ok(self):
        importer = self.importer
        self.assertRaises(FeedNotFoundError, importer.import_feed,
                FEED_YIELDING_404)
