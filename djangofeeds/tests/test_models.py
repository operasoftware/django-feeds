import unittest2 as unittest
import httplib as http
import pytz
from datetime import datetime
from uuid import uuid4

from djangofeeds import models
from djangofeeds.utils import naturaldate
from django.utils.timezone import utc


def gen_unique_id():
    return str(uuid4())


class TestCategory(unittest.TestCase):

    def test__unicode__(self):
        cat = models.Category(name="foo", domain="bar")
        self.assertIn("foo", unicode(cat))
        self.assertIn("bar", unicode(cat))

        cat = models.Category(name="foo")
        self.assertIn("foo", unicode(cat))


class TestEnclosure(unittest.TestCase):

    def test__unicode__(self):
        en = models.Enclosure(url="http://e.com/media/i.jpg",
                type="image/jpeg", length=376851)
        self.assertIn("http://e.com/media/i.jpg", unicode(en))
        self.assertIn("image/jpeg", unicode(en))
        self.assertIn("376851", unicode(en))


class TestPost(unittest.TestCase):

    def setUp(self):
        self.feed = models.Feed.objects.create(name="testfeed",
                                               feed_url=gen_unique_id(),
                                               sort=0)

    def test__unicode__(self):
        post = models.Post(feed=self.feed, title="foo")
        self.assertIn("foo", unicode(post))

    def test_auto_guid(self):
        p1 = models.Post(feed=self.feed, title="foo")
        p2 = models.Post(feed=self.feed, title="bar")

        self.assertNotEqual(p1.auto_guid(), p2.auto_guid())

    def test_date_published_naturaldate(self):
        now = datetime.now(pytz.utc)
        day = datetime(now.year, now.month, now.day, tzinfo=utc)
        post = models.Post(feed=self.feed, title="baz", date_published=now)
        self.assertEqual(post.date_published_naturaldate, naturaldate(day))

    def test_date_updated_naturaldate(self):
        now = datetime.now(pytz.utc)
        post = models.Post(feed=self.feed, title="baz", date_updated=now)
        self.assertEqual(post.date_updated_naturaldate, naturaldate(now))


class TestFeed(unittest.TestCase):

    def test__unicode__(self):
        f = models.Feed(name="foo", feed_url="http://example.com")
        self.assertIn("foo", unicode(f))
        self.assertIn("(http://example.com)", unicode(f))

    def test_error_for_status(self):
        f = models.Feed(name="foo", feed_url="http://example.com")
        self.assertEqual(f.error_for_status(http.NOT_FOUND),
                          models.FEED_NOT_FOUND_ERROR)
        self.assertEqual(f.error_for_status(http.INTERNAL_SERVER_ERROR),
                          models.FEED_GENERIC_ERROR)
        self.assertIsNone(f.error_for_status(http.OK))

    def test_save_generic_error(self):
        f = models.Feed(name="foo1", feed_url="http://example.com/t1.rss",
                sort=0)
        f.save_generic_error()

        indb = models.Feed.objects.get(feed_url="http://example.com/t1.rss")
        self.assertEqual(indb.last_error, models.FEED_GENERIC_ERROR)

    def test_set_error_status(self):
        f = models.Feed(name="foo3", feed_url="http://example.com/t3.rss",
                sort=0)
        f.set_error_status(http.INTERNAL_SERVER_ERROR)

        indb = models.Feed.objects.get(feed_url="http://example.com/t3.rss")
        self.assertEqual(indb.last_error, models.FEED_GENERIC_ERROR)

    def test_save_timeout_error(self):
        f = models.Feed(name="foo2", feed_url="http://example.com/t2.rss",
                sort=0)
        f.save_timeout_error()

        indb = models.Feed.objects.get(feed_url="http://example.com/t2.rss")
        self.assertEqual(indb.last_error, models.FEED_TIMEDOUT_ERROR)

    def test_date_last_refresh_naturaldate(self):
        now = datetime.now(pytz.utc)
        f = models.Feed(name="foo2", feed_url="http://example.com/t2.rss",
                sort=0, date_last_refresh=now)
        self.assertEqual(f.date_last_refresh_naturaldate, naturaldate(now))

    def test_objects_since(self):
        self.assertFalse(models.Feed.objects.all().since(1))

    def test_objects_ratio(self):
        models.Feed.objects.all().delete()
        [models.Feed.objects.create(name=gen_unique_id(),
                                    feed_url=gen_unique_id(),
                                    sort=0, ratio=i)
                    for i in (0, 0.23, 0.24, 0.25, 1.12, 2.43)]
        self.assertEqual(models.Feed.objects.ratio(min=0).count(), 5)
        self.assertEqual(
                models.Feed.objects.ratio(min=0.23, max=0.25).count(), 1)
        self.assertEqual(models.Feed.objects.ratio(max=0.24).count(), 2)

    def test_expire_old_posts_no_posts(self):
        f = models.Feed.objects.create(name="foozalaz",
                feed_url=gen_unique_id(), sort=0)
        self.assertEqual(f.expire_old_posts(), 0)

    def test_expire_old_posts(self):
        now = datetime.now(pytz.utc)
        f = models.Feed.objects.create(name="foozalaz",
                feed_url=gen_unique_id(), sort=0)
        [models.Post.objects.create(feed=f,
                                    title=gen_unique_id(),
                                    date_published=now,
                                    date_updated=now)
                    for i in range(10)]
        self.assertEqual(f.expire_old_posts(min_posts=5, max_posts=5), 5)
        self.assertEqual(models.Post.objects.filter(feed=f).count(), 5)
        self.assertEqual(f.expire_old_posts(min_posts=3, max_posts=3), 2)
        self.assertEqual(models.Post.objects.filter(feed=f).count(), 3)
