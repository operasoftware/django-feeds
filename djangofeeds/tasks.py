from celery.task import tasks, Task, PeriodicTask, TaskSet
from djangofeeds.importers import FeedImporter
from djangofeeds.messaging import refresh_all_feeds_delayed
from djangofeeds.models import Feed
from django.conf import settings
from django.core.cache import cache
from celery.conf import AMQP_PUBLISHER_ROUTING_KEY
from celery.utils import chunks
import math
from datetime import datetime, timedelta

DEFAULT_REFRESH_EVERY = 3 * 60 * 60 # 3 hours
DEFAULT_FEED_TIMEOUT = 10
REFRESH_EVERY = getattr(settings, "DJANGOFEEDS_REFRESH_EVERY",
                        DEFAULT_REFRESH_EVERY)
ROUTING_KEY_PREFIX = getattr(settings, "DJANGOFEEDS_ROUTING_KEY_PREFIX",
                             AMQP_PUBLISHER_ROUTING_KEY)
FEED_TIMEOUT = getattr(settings, "DJANGOFEEDS_FEED_TIMEOUT",
                       DEFAULT_FEED_TIMEOUT)
FEED_LOCK_CACHE_KEY_FMT = "djangofeeds.import_lock.%s"
FEED_LOCK_EXPIRE = 60 * 3; # lock expires in 3 minutes.


class RefreshFeedTask(Task):
    """Refresh a djangofeed feed, supports multiprocessing."""
    name = "djangofeeds.refresh_feed"
    routing_key = ".".join([ROUTING_KEY_PREFIX, "feedimporter"])
    ignore_result = True

    def run(self, feed_url, feed_id=None, **kwargs):
        feed_id = feed_id or feed_url
        lock_id = FEED_LOCK_CACHE_KEY_FMT % feed_id

        is_locked = lambda: str(cache.get(lock_id)) == "true"
        acquire_lock = lambda: cache.set(lock_id, "true", FEED_LOCK_EXPIRE)
        release_lock = lambda: cache.set(lock_id, "nil", 1)

        logger = self.get_logger(**kwargs)
        logger.info("Importing feed %s" % feed_url)
        if is_locked():
            logger.info("Feed is already being imported by another process.")
            return feed_url

        acquire_lock()
        try:
            importer = FeedImporter(update_on_import=True, logger=logger)
            importer.import_feed(feed_url)
        finally:
            release_lock()

        return feed_url
tasks.register(RefreshFeedTask)


class RefreshAllFeeds(PeriodicTask):
    name = "djangofeeds.refresh_all_feeds"
    run_every = REFRESH_EVERY
    ignore_result = True

    def run(self, **kwargs):
        from carrot.connection import DjangoAMQPConnection
        connection = DjangoAMQPConnection()
        try:
            now = datetime.now()
            threshold = now - timedelta(seconds=REFRESH_EVERY)
            feeds = Feed.objects.filter(date_last_refresh__lt=threshold)
            total = feeds.count()
            if not total:
                return

            # We evenly distribute the refreshing of feeds over the time
            # interval available.

            # Time window is 75% of refresh interval in minutes.
            interval = REFRESH_EVERY
            time_window = interval * 0.75 / 60

            # Make buckets with total/time_window feeds in each.
            blocksize = total / time_window
            buckets = chunks(feeds.iterator(), int(blocksize))

            for minutes, bucket in enumerate(buckets):
                # Skew the countdown for feeds in this.
                seconds = 60 * (minutes+1)
                for feed in bucket:
                    RefreshFeedTask.apply_async(args=[feed.feed_url],
                                                connection=connection,
                                                countdown=seconds)
        finally:
            connection.close()
tasks.register(RefreshAllFeeds)
