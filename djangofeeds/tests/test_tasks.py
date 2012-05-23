import unittest2 as unittest

CELERY_MISSING = False
try:
    from djangofeeds import tasks
except ImportError:
    CELERY_MISSING = True


class MockImporter(object):
    imported = []

    def __init__(self, *args, **kwargs):
        pass

    def import_feed(self, url, **kwargs):
        self.__class__.imported.append(url)


class TestRefreshFeed(unittest.TestCase):

    @unittest.skipIf(CELERY_MISSING, "Celery is missing")
    def test_refresh(self):
        tasks.refresh_feed.apply(args=["http://example.com/t.rss"],
                                kwargs={"importer_cls": MockImporter}).get()

        self.assertIn("http://example.com/t.rss", MockImporter.imported)

    @unittest.skipIf(CELERY_MISSING, "Celery is missing")
    def test_refresh_with_locks(self):
        prev = tasks.ENABLE_LOCKS
        tasks.ENABLE_LOCKS = True
        try:
            tasks.refresh_feed.apply(args=["http://example.com/t.rss"],
                                kwargs={"importer_cls": MockImporter}).get()

            self.assertIn("http://example.com/t.rss", MockImporter.imported)
        finally:
            tasks.ENABLE_LOCKS = prev

    @unittest.skipIf(CELERY_MISSING, "Celery is not installed")
    def test_refresh_with_locked(self):

        class MockCache(tasks.cache.__class__):

            def __init__(self):
                pass

            def get(self, key, *args, **kwargs):
                return "true"

        prev = tasks.cache
        tasks.cache = MockCache()
        try:
            tasks.refresh_feed.apply(args=["http://example.com/t.rss"],
                                kwargs={"importer_cls": MockImporter}).get()
            self.assertIn(
                    "http://example.com/t.rss", MockImporter.imported)
        finally:
            tasks.cache = prev
