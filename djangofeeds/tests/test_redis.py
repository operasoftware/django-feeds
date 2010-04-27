from __future__ import with_statement

import unittest2 as unittest
from datetime import datetime

from djangofeeds.backends.pyredis import RedisBackend


class TestRedisBackend(unittest.TestCase):

    def setUp(self):
        self.b = RedisBackend()
        self.b.clear()

    def test_entry_lifecycle(self):
        data = dict(feed_url="http://rss.com/example",
                    title="Example Post",
                    guid="http://rss.com/example/1",
                    link="http://rss.com/example/1",
                    content="This is an example",
                    timestamp=datetime.now())
        entry = self.b.Entry(**data)
        entry_id = entry.save()
        self.assertEqual(entry_id, entry.id)

        stored = self.b.get(entry_id)
        self.assertDictContainsSubset(data, stored)

        stored.content = "Content has been changed"
        changed_data = dict(stored)
        new_id = stored.save()
        self.assertEqual(stored.id, new_id)
        again = self.b.get(new_id)
        self.assertDictContainsSubset(changed_data, again)
        self.assertEqual(again.content, "Content has been changed")

        with self.assertRaises(KeyError):
            self.b.get("does-not-exist")

        stored.delete()
        with self.assertRaises(KeyError):
            self.b.get(stored.id)
