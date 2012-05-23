from __future__ import with_statement

import unittest2 as unittest
import pytz
from datetime import datetime, timedelta
from functools import wraps
from itertools import count
import socket

from nose import SkipTest


try:
    from redis.exceptions import ConnectionError
except ImportError:
    class ConnectionError(socket.error):
        pass

try:
    import redis
except ImportError:
    Entries = None
else:
    from djangofeeds.backends.pyredis import Entries


def skip_if_redis_not_running(fun):

    @wraps(fun)
    def _inner(*args, **kwargs):
        if Entries is None:
            raise SkipTest("The redis library is not installed.")
        try:
            return fun(*args, **kwargs)
        except ConnectionError, exc:
            raise SkipTest("Can't connect to redis server: %s" % (exc, ))


class TestRedisBackend(unittest.TestCase):
    next_id = count(1).next

    test_data = dict(feed_url="http://rss.com/example/%d",
                    title="Example Post",
                    guid="http://rss.com/example/%d",
                    link="http://rss.com/example/%d",
                    content="This is an example",
                    timestamp=datetime.now(pytz.utc))

    def setUp(self):
        self.b = Entries()
        self.b.clear()

    def create_post(self, delta=None, **fields):
        id = self.next_id()
        fields.setdefault("guid", self.test_data["guid"] % (id, ))
        fields.setdefault("link", self.test_data["link"] % (id, ))
        fields.setdefault("feed_url", self.test_data["feed_url"] % (id, ))
        fields.setdefault("timestamp", datetime.now(pytz.utc))
        fields.setdefault("date_updated", fields["timestamp"])
        if delta is not None:
            fields["timestamp"] = fields["timestamp"] + delta
        ret = dict(self.test_data, **fields)
        return ret

    @skip_if_redis_not_running
    def test_is_sorted(self):
        f = "http://google.com/reader/rss/123"
        posts = [self.create_post(feed_url=f, delta=timedelta(hours=-1)),
                 self.create_post(feed_url=f, delta=timedelta(hours=-2)),
                 self.create_post(feed_url=f, delta=timedelta(hours=-3)),
                 self.create_post(feed_url=f, delta=timedelta(hours=-4)),
                 self.create_post(feed_url=f, delta=timedelta(hours=-5))]

        class MockFeed(object):
            def __init__(self, feed_url):
                self.feed_url = feed_url

        entries = [self.b.update_or_create(MockFeed(f), **fields)
                        for fields in posts]

        ordered = self.b.all_by_order(entries[0].feed_url)
        self.assertEqual(len(ordered), len(posts))

    @skip_if_redis_not_running
    def test_entry_lifecycle(self):
        data = self.create_post()
        posts = self.b
        entry = posts.Entry(**data)
        entry_id = entry.save()
        self.assertEqual(entry_id, entry.id)

        lookup = posts.get_by_guid(data["feed_url"], data["guid"])
        self.assertEqual(lookup.id, entry.id)

        stored = posts.get(entry_id)
        self.assertDictContainsSubset(data, stored)

        stored.content = "Content has been changed"
        changed_data = dict(stored)
        new_id = stored.save()
        self.assertEqual(stored.id, new_id)
        again = posts.get(new_id)
        self.assertDictContainsSubset(changed_data, again)
        self.assertEqual(again.content, "Content has been changed")

        with self.assertRaises(KeyError):
            posts.get("does-not-exist")

        stored.delete()
        with self.assertRaises(KeyError):
            posts.get(stored.id)
