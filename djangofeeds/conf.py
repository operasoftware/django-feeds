from django.conf import settings
from datetime import timedelta

DEFAULT_DEFAULT_POST_LIMIT = 20
DEFAULT_NUM_POSTS = -1
DEFAULT_CACHE_MIN = 30
DEFAULT_ENTRY_WORD_LIMIT = 100
DEFAULT_FEED_TIMEOUT = 10
DEFAULT_MIN_REFRESH_INTERVAL = timedelta(seconds=60 * 20)

"""
.. data:: STORE_ENCLOSURES

Keep post enclosures.
Default: False
Taken from: ``settings.DJANGOFEEDS_STORE_ENCLOSURES``.
"""

STORE_ENCLOSURES = getattr(settings, "DJANGOFEEDS_STORE_ENCLOSURES", False)

"""
.. data:: STORE_CATEGORIES

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


"""
.. data:: DEFAULT_POST_LIMIT

The default number of posts to import.
Taken from: ``settings.DJANGOFEEDS_DEFAULT_POST_LIMIT``.
"""
DEFAULT_POST_LIMIT = getattr(settings, "DJANGOFEEDS_DEFAULT_POST_LIMIT",
                       DEFAULT_DEFAULT_POST_LIMIT)
