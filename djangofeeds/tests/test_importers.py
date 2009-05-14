from __future__ import with_statement
import os
import unittest
from djangofeeds.importers import FeedImporter
from djangofeeds.models import Feed, Post, Enclosure
from yadayada.test.user import create_random_user
from django.contrib.auth import authenticate

data_path = os.path.join(os.path.dirname(__file__), 'data')


def get_data_filename(name):
    return os.sep.join([data_path, name])


def get_data_file(name, mode="r"):
    with open(get_data_filename(name), mode) as file:
        return file.read()


class TestFeedImporter(unittest.TestCase):

    def setUp(self):
        randuser = create_random_user()
        self.user = authenticate(username=randuser.username,
                                 password=randuser.username)
        self.assertEqual(randuser.username, self.user.username)
        self.assertTrue(self.user.is_authenticated(),
                        "Random user created successfully")
        self.feed = get_data_filename("example_feed.rss")
        self.importer = FeedImporter()

    def test_import_feed(self):
        feed = self.feed
        importer = self.importer
        feed_obj = importer.import_feed(feed)
        self.assertEqual(feed_obj.name, "Lifehacker", "feed title is set")
        self.assertEqual(feed_obj.post_set.count(), 20, "feed has 20 items")
        self.assertEqual(feed_obj.feed_url, feed, "feed url is filename")
        self.assertTrue(feed_obj.description, "feed has description")

        posts = feed_obj.post_set.all()
        first_post = posts[0]
        self.assertEqual(first_post.guid, "Lifehacker-5147831")
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
