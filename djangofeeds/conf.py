from datetime import timedelta

from django.conf import settings

try:
    from celery import conf as celeryconf
    DEFAULT_ROUTING_KEY = celeryconf.DEFAULT_ROUTING_KEY
except ImportError:
    DEFAULT_ROUTING_KEY = "celery"

DEFAULT_DEFAULT_POST_LIMIT = 20
DEFAULT_NUM_POSTS = -1
DEFAULT_CACHE_MIN = 30
DEFAULT_ENTRY_WORD_LIMIT = 100
DEFAULT_FEED_TIMEOUT = 10
DEFAULT_REFRESH_EVERY = 3 * 60 * 60             # 3 hours
DEFAULT_FEED_LOCK_EXPIRE = 60 * 3               # lock expires in 3 minutes.
DEFAULT_MIN_REFRESH_INTERVAL = timedelta(seconds=60 * 20)
DEFAULT_FEED_LOCK_CACHE_KEY_FMT = "djangofeeds.import_lock.%s"

""" .. data:: STORE_ENCLOSURES

    Keep post enclosures.
    Default: False
    Taken from: ``settings.DJANGOFEEDS_STORE_ENCLOSURES``.

"""
STORE_ENCLOSURES = getattr(settings, "DJANGOFEEDS_STORE_ENCLOSURES", False)

""" .. data:: STORE_CATEGORIES

    Keep feed/post categories
    Default: False
    Taken from: ``settings.DJANGOFEEDS_STORE_CATEGORIES``.

"""
STORE_CATEGORIES = getattr(settings, "DJANGOFEEDS_STORE_CATEGORIES", False)

"""
.. data:: MIN_REFRESH_INTERVAL

    Feed should not be refreshed if it was last refreshed within this time.
    (in seconds)
    Default: 20 minutes
    Taken from: ``settings.DJANGOFEEDS_MIN_REFRESH_INTERVAL``.

"""
MIN_REFRESH_INTERVAL = getattr(settings, "DJANGOFEEDS_MIN_REFRESH_INTERVAL",
                               DEFAULT_MIN_REFRESH_INTERVAL)

"""
.. data:: FEED_TIMEOUT

    Timeout in seconds for the feed to refresh.
    Default: 10 seconds
    Taken from: ``settings.DJANGOFEEDS_FEED_TIMEOUT``.
"""
FEED_TIMEOUT = getattr(settings, "DJANGOFEEDS_FEED_TIMEOUT",
                       DEFAULT_FEED_TIMEOUT)


def _interval(interval):
    if isinstance(interval, int):
        return timedelta(seconds=interval)
    return interval

# Make sure MIN_REFRESH_INTERVAL is a timedelta object.
MIN_REFRESH_INTERVAL = _interval(MIN_REFRESH_INTERVAL)


""" .. data:: DEFAULT_POST_LIMIT

    The default number of posts to import.
    Taken from: ``settings.DJANGOFEEDS_DEFAULT_POST_LIMIT``.

"""
DEFAULT_POST_LIMIT = getattr(settings, "DJANGOFEEDS_DEFAULT_POST_LIMIT",
                       DEFAULT_DEFAULT_POST_LIMIT)


""" .. data:: REFRESH_EVERY

    Interval in seconds between feed refreshes.
    Default: 3 hours
    Taken from: ``settings.DJANGOFEEDS_REFRESH_EVERY``.

"""
REFRESH_EVERY = getattr(settings, "DJANGOFEEDS_REFRESH_EVERY",
                        DEFAULT_REFRESH_EVERY)


"""".. data:: FEED_LAST_REQUESTED_REFRESH_LIMIT

    the maximum amount of time a feed can be unused
    before stopping refreshing it. Used by opal-feed.
"""
FEED_LAST_REQUESTED_REFRESH_LIMIT = getattr(settings,
                    "FEED_LAST_REQUESTED_REFRESH_LIMIT", None)


""" .. data:: ROUTING_KEY_PREFIX

    Prefix for AMQP routing key.
    Default: ``celery.conf.AMQP_PUBLISHER_ROUTING_KEY``.
    Taken from: ``settings.DJANGOFEEDS_ROUTING_KEY_PREFIX``.

"""
ROUTING_KEY_PREFIX = getattr(settings, "DJANGOFEEDS_ROUTING_KEY_PREFIX",
                            DEFAULT_ROUTING_KEY)

""" .. data:: FEED_LOCK_CACHE_KEY_FMT

    Format used for feed cache lock. Takes one argument: the feeds URL.
    Default: "djangofeeds.import_lock.%s"
    Taken from: ``settings.DJANGOFEEDS_FEED_LOCK_CACHE_KEY_FMT``.

"""
FEED_LOCK_CACHE_KEY_FMT = getattr(settings,
                            "DJANGOFEEDS_FEED_LOCK_CACHE_KEY_FMT",
                            DEFAULT_FEED_LOCK_CACHE_KEY_FMT)

""" .. data:: FEED_LOCK_EXPIRE

    Time in seconds which after the feed lock expires.
    Default: 3 minutes
    Taken from: ``settings.DJANGOFEEDS_FEED_LOCK_EXPIRE``.

"""
FEED_LOCK_EXPIRE = getattr(settings,
                    "DJANGOFEEDS_FEED_LOCK_EXPIRE",
                    DEFAULT_FEED_LOCK_EXPIRE)


POST_STORAGE_BACKEND = getattr(settings,
                            "DJANGOFEEDS_POST_STORAGE_BACKEND",
                            "djangofeeds.backends.database.DatabaseBackend")

REDIS_POST_HOST = getattr(settings,
                          "DJANGOFEEDS_REDIS_POST_HOST",
                          "localhost")
REDIS_POST_PORT = getattr(settings,
                          "DJANGOFEEDS_REDIS_POST_PORT",
                          None)
REDIS_POST_DB = getattr(settings,
                        "DJANGOFEEDS_REDIS_POST_DB",
                        "djangofeeds:post")

FSCK_ON_UPDATE = getattr(settings,
                         "DJANGOFEEDS_FSCK_ON_UPDATE",
                         False)
