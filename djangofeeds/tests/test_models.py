import unittest
import httplib as http
from datetime import datetime

from celery.utils import gen_unique_id

from djangofeeds import models
from djangofeeds.utils import naturaldate


class TestCategory(unittest.TestCase):

    def test__unicode__(self):
        cat = models.Category(name="foo", domain="bar")
        self.assertTrue("foo" in unicode(cat))
        self.assertTrue("bar" in unicode(cat))

        cat = models.Category(name="foo")
        self.assertTrue("foo" in unicode(cat))


class TestEnclosure(unittest.TestCase):

    def test__unicode__(self):
        en = models.Enclosure(url="http://e.com/media/i.jpg",
                type="image/jpeg", length=376851)
        self.assertTrue("http://e.com/media/i.jpg" in unicode(en))
        self.assertTrue("image/jpeg" in unicode(en))
        self.assertTrue("376851" in unicode(en))


class TestPost(unittest.TestCase):

    def setUp(self):
        self.feed = models.Feed.objects.create(name="testfeed",
                                               feed_url=gen_unique_id(),
                                               sort=0)

    def test__unicode__(self):
        post = models.Post(feed=self.feed, title="foo")
        self.assertTrue("foo" in unicode(post))

    def test_auto_guid(self):
        p1 = models.Post(feed=self.feed, title="foo")
        p2 = models.Post(feed=self.feed, title="bar")

        self.assertFalse(p1.auto_guid() == p2.auto_guid())

    def test_date_published_naturaldate(self):
        now = datetime.now()
        day = datetime(now.year, now.month, now.day)
        post = models.Post(feed=self.feed, title="baz", date_published=now)
        self.assertEquals(post.date_published_naturaldate, naturaldate(day))

    def test_date_updated_naturaldate(self):
        now = datetime.now()
        post = models.Post(feed=self.feed, title="baz", date_updated=now)
        self.assertEquals(post.date_updated_naturaldate, naturaldate(now))


class TestFeed(unittest.TestCase):

    def test__unicode__(self):
        f = models.Feed(name="foo", feed_url="http://example.com")
        self.assertTrue("foo" in unicode(f))
        self.assertTrue("(http://example.com)" in unicode(f))

    def test_error_for_status(self):
        f = models.Feed(name="foo", feed_url="http://example.com")
        self.assertEquals(f.error_for_status(http.NOT_FOUND),
                          models.FEED_NOT_FOUND_ERROR)
        self.assertEquals(f.error_for_status(http.INTERNAL_SERVER_ERROR),
                          models.FEED_GENERIC_ERROR)
        self.assertTrue(f.error_for_status(http.OK) is None)

    def test_save_generic_error(self):
        f = models.Feed(name="foo1", feed_url="http://example.com/t1.rss",
                sort=0)
        f.save_generic_error()

        indb = models.Feed.objects.get(feed_url="http://example.com/t1.rss")
        self.assertEquals(indb.last_error, models.FEED_GENERIC_ERROR)

    def test_set_error_status(self):
        f = models.Feed(name="foo3", feed_url="http://example.com/t3.rss",
                sort=0)
        f.set_error_status(http.INTERNAL_SERVER_ERROR)

        indb = models.Feed.objects.get(feed_url="http://example.com/t3.rss")
        self.assertEquals(indb.last_error, models.FEED_GENERIC_ERROR)

    def test_save_timeout_error(self):
        f = models.Feed(name="foo2", feed_url="http://example.com/t2.rss",
                sort=0)
        f.save_timeout_error()

        indb = models.Feed.objects.get(feed_url="http://example.com/t2.rss")
        self.assertEquals(indb.last_error, models.FEED_TIMEDOUT_ERROR)

    def test_date_last_refresh_naturaldate(self):
        now = datetime.now()
        f = models.Feed(name="foo2", feed_url="http://example.com/t2.rss",
                sort=0, date_last_refresh=now)
        self.assertEquals(f.date_last_refresh_naturaldate, naturaldate(now))

    def test_objects_since(self):
        self.assertFalse(models.Feed.objects.all().since(1))

    def test_objects_ratio(self):
        models.Feed.objects.all().delete()
        feeds = [models.Feed.objects.create(name=gen_unique_id(),
                                            feed_url=gen_unique_id(),
                                            sort=0, ratio=i)
                    for i in (0, 0.23, 0.24, 0.25, 1.12, 2.43)]
        self.assertEquals(models.Feed.objects.ratio(min=0).count(), 5)
        self.assertEquals(
                models.Feed.objects.ratio(min=0.23, max=0.25).count(), 1)
        self.assertEquals(models.Feed.objects.ratio(max=0.24).count(), 2)

    def test_expire_old_posts_no_posts(self):
        f = models.Feed.objects.create(name="foozalaz",
                feed_url=gen_unique_id(), sort=0)
        self.assertEquals(f.expire_old_posts(), 0)

    def test_expire_old_posts(self):
        now = datetime.now()
        f = models.Feed.objects.create(name="foozalaz",
                feed_url=gen_unique_id(), sort=0)
        posts = [models.Post.objects.create(feed=f,
                                            title=gen_unique_id(),
                                            date_published=now,
                                            date_updated=now)
                    for i in range(10)]
        self.assertEquals(f.expire_old_posts(min_posts=5), 5)
        self.assertEquals(models.Post.objects.filter(feed=f).count(), 5)

