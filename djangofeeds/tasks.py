from math import floor, ceil
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache

from celery import conf as celeryconf
from celery.utils import noop
from celery.decorators import task

from djangofeeds.models import Feed
from djangofeeds.importers import FeedImporter

DEFAULT_REFRESH_EVERY = 3 * 60 * 60 # 3 hours
DEFAULT_FEED_LOCK_CACHE_KEY_FMT = "djangofeeds.import_lock.%s"
DEFAULT_FEED_LOCK_EXPIRE = 60 * 3 # lock expires in 3 minutes.

ENABLE_LOCKS = False

"""
.. data:: REFRESH_EVERY

Interval in seconds between feed refreshes.
Default: 3 hours
Taken from: ``settings.DJANGOFEEDS_REFRESH_EVERY``.

"""
REFRESH_EVERY = getattr(settings, "DJANGOFEEDS_REFRESH_EVERY",
                        DEFAULT_REFRESH_EVERY)


"""
.. data:: REFRESH_EVERY

Prefix for AMQP routing key.
Default: ``celery.conf.AMQP_PUBLISHER_ROUTING_KEY``.
Taken from: ``settings.DJANGOFEEDS_ROUTING_KEY_PREFIX``.

"""
ROUTING_KEY_PREFIX = getattr(settings, "DJANGOFEEDS_ROUTING_KEY_PREFIX",
                             celeryconf.DEFAULT_ROUTING_KEY)

"""
.. data:: FEED_LOCK_CACHE_KEY_FMT

Format used for feed cache lock. Takes one argument: the feeds URL.
Default: "djangofeeds.import_lock.%s"
Taken from: ``settings.DJANGOFEEDS_FEED_LOCK_CACHE_KEY_FMT``.

"""
FEED_LOCK_CACHE_KEY_FMT = getattr(settings,
                            "DJANGOFEEDS_FEED_LOCK_CACHE_KEY_FMT",
                            DEFAULT_FEED_LOCK_CACHE_KEY_FMT)

"""
.. data:: FEED_LOCK_EXPIRE

Time in seconds which after the feed lock expires.
Default: 3 minutes
Taken from: ``settings.DJANGOFEEDS_FEED_LOCK_EXPIRE``.

"""
FEED_LOCK_EXPIRE = getattr(settings,
                    "DJANGOFEEDS_FEED_LOCK_EXPIRE",
                    DEFAULT_FEED_LOCK_EXPIRE)


@task(routing_key="%s.feedimporter" % ROUTING_KEY_PREFIX, ignore_result=True)
def refresh_feed(feed_url, feed_id=None, **kwargs):
    """Refresh a djangofeed feed, supports multiprocessing.

    :param feed_url: The URL of the feed to refresh.
    :keyword feed_id: Optional id of the feed, if not specified
        the ``feed_url`` is used instead.

    """
    feed_id = feed_id or feed_url
    lock_id = FEED_LOCK_CACHE_KEY_FMT % feed_id

    if ENABLE_LOCKS:
        is_locked = lambda: str(cache.get(lock_id)) == "true"
        acquire_lock = lambda: cache.set(lock_id, "true", FEED_LOCK_EXPIRE)
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
        importer = FeedImporter(update_on_import=True, logger=logger)
        importer.import_feed(feed_url)
    finally:
        release_lock()

    return feed_url
