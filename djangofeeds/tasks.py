from celery.task import tasks, Task, PeriodicTask
from djangofeeds.importers import FeedImporter
from djangofeeds.messaging import refresh_all_feeds_delayed
from django.conf import settings

DEFAULT_REFRESH_EVERY = 15 * 60 # 15 minutes
REFRESH_EVERY = getattr(settings, "DJANGOFEEDS_REFRESH_EVERY",
                        DEFAULT_REFRESH_EVERY)


class RefreshFeedTask(Task):
    """Refresh a djangofeed feed, supports multiprocessing."""
    name = "djangofeeds.refresh_feed"
    routing_key = "feed.importer"

    def run(self, **kwargs):
        feed_url = kwargs["feed_url"]
        logger = self.get_logger(**kwargs)
        logger.info(">>> Importing feed: %s..." % feed_url)
        importer = FeedImporter(update_on_import=True, logger=logger)
        importer.import_feed(feed_url)
        return feed_url
tasks.register(RefreshFeedTask)


class RefreshAllFeeds(PeriodicTask):
    name = "djangofeeds.refresh_all_feeds"
    run_every = REFRESH_EVERY

    def run(self, **kwargs):
        refresh_all_feeds_delayed()
tasks.register(RefreshAllFeeds)
