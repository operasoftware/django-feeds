from celery.task import tasks, Task, PeriodicTask
from celery.timer import TimeoutError
from djangofeeds.importers import FeedImporter
from djangofeeds.messaging import refresh_all_feeds_delayed
from django.conf import settings
import threading

DEFAULT_REFRESH_EVERY = 15 * 60 # 15 minutes
DEFAULT_FEED_TIMEOUT = 10
DEFAULT_ROUTING_KEY_PREFIX = "feed"
REFRESH_EVERY = getattr(settings, "DJANGOFEEDS_REFRESH_EVERY",
                        DEFAULT_REFRESH_EVERY)
ROUTING_KEY_PREFIX = getattr(settings, "DJANGOFEEDS_ROUTING_KEY_PREFIX",
                             DEFAULT_ROUTING_KEY_PREFIX)
FEED_TIMEOUT = getattr(settings, "DJANGOFEEDS_FEED_TIMEOUT",
                       DEFAULT_FEED_TIMEOUT)


class RefreshFeedTask(Task):
    """Refresh a djangofeed feed, supports multiprocessing."""
    name = "djangofeeds.refresh_feed"
    routing_key = ".".join([DJANGOFEEDS_ROUTING_KEY_PREFIX, "feedimporter"])

    def run(self, **kwargs):
        feed_url = kwargs["feed_url"]

        def on_timeout():
            raise TimeoutError(
                    "Timed out while importing feed: %s" % feed_url)

        logger = self.get_logger(**kwargs)
        logger.info("Importing feed %s" % feed_url)

        timeout_timer = threading.Timer(FEED_TIMEOUT, on_timeout)
        timeout_timer.start()
        try:
            importer = FeedImporter(update_on_import=True, logger=logger)
            importer.import_feed(feed_url)
        finally:
            timeout_timer.cancel()
        return feed_url
tasks.register(RefreshFeedTask)


class RefreshAllFeeds(PeriodicTask):
    name = "djangofeeds.refresh_all_feeds"
    run_every = REFRESH_EVERY

    def run(self, **kwargs):
        import socket
        socket.setdefaulttimeout(10)
        refresh_all_feeds_delayed()
tasks.register(RefreshAllFeeds)
