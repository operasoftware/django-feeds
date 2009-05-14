from celery.task import tasks, Task, PeriodicTask
from djangofeeds.importers import FeedImporter
from djangofeeds.messaging import refresh_all_feeds_delayed


class RefreshFeedTask(Task):
    """Refresh a djangofeed feed, supports multiprocessing."""
    name = "djangofeeds.refresh_feed"

    def run(self, **kwargs):
        feed_url = kwargs["feed_url"]
        logger = self.get_logger(**kwargs)
        logger.info(">>> Importing feed: %s..." % feed_url)
        importer = FeedImporter(update_on_import=True)
        importer.import_feed(feed_url)
        return feed_url
tasks.register(RefreshFeedTask)


class RefreshAllFeeds(PeriodicTask):
    name = "djangofeeds.refresh_all_feeds"
    run_every = 15 * 60 # 15 minutes

    def run(self, **kwargs):
        refresh_all_feeds_delayed()
tasks.register(RefreshAllFeeds)


class SetSomeSum(Task):
    name = "djangofeeds.set_some_sum"

    def run(self, increment):
        from djangofeeds.models import SomeSum
        o, c = SomeSum.objects.get_or_create(pk=1)
        c.the_sum = increment
        c.the_sum2 += increment
        c.save()
