from django.core.cache import cache

from celery.utils import noop
from celery.decorators import task

from djangofeeds import conf
from djangofeeds.conf import ROUTING_KEY_PREFIX
from djangofeeds.importers import FeedImporter

ENABLE_LOCKS = False


@task(routing_key="%s.feedimporter" % ROUTING_KEY_PREFIX, ignore_result=True)
def refresh_feed(feed_url, feed_id=None, importer_cls=None, **kwargs):
    """Refresh a djangofeed feed, supports multiprocessing.

    :param feed_url: The URL of the feed to refresh.
    :keyword feed_id: Optional id of the feed, if not specified
        the ``feed_url`` is used instead.

    """
    importer_cls = importer_cls or FeedImporter
    feed_id = feed_id or feed_url
    lock_id = conf.FEED_LOCK_CACHE_KEY_FMT % feed_id
    lock_expires = conf.FEED_LOCK_EXPIRE

    if ENABLE_LOCKS:
        is_locked = lambda: str(cache.get(lock_id)) == "true"
        acquire_lock = lambda: cache.set(lock_id, "true", lock_expires)
        release_lock = lambda: cache.set(lock_id, "nil", 1)
    else:
        acquire_lock = release_lock = noop
        is_locked = lambda: False

    logger = refresh_feed.get_logger(**kwargs)
    logger.info("Importing feed %s" % feed_url)
    if is_locked():
        logger.error("Feed is already being imported by another process.")
        return feed_url


    acquire_lock()
    try:
        importer = importer_cls(update_on_import=True, logger=logger)
        importer.import_feed(feed_url)
    finally:
        release_lock()

    return feed_url
