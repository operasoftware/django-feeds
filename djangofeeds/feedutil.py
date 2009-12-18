from django.utils.text import truncate_html_words
from djangofeeds import conf
from datetime import datetime
from djangofeeds.optimization import BeaconDetector
import time
from datetime import datetime, timedelta

_beacon_detector = BeaconDetector()


def format_date(t):
    if isinstance(t, time.struct_time):
        return datetime(*t[:6])
    return t


def entries_by_date(entries, limit=None):
    """Sort the feed entries by date

    :param entries: Entries given from :mod:`feedparser``.
    :param limit: Limit number of posts.

    """
    now = datetime.now()

    def find_date(entry, counter):
        """Find the most current date entry tuple."""

        return (entry.get("updated_parsed") or
                entry.get("published_parsed") or
                entry.get("date_parsed") or
                now - timedelta(seconds=(counter * 30)))


    sorted_entries = [(format_date(find_date(entry, counter)), entry)
                        for counter, entry in enumerate(entries)]

    sorted_entries.sort(key=lambda k: k[0])
    sorted_entries.reverse()
    return [entry for _date, entry in sorted_entries[:limit]]


def find_post_content(feed_obj, entry):
    """Find the correct content field for a post."""
    try:
        content = entry["content"][0]["value"]
    except (IndexError, KeyError):
        content = entry.get("description") or entry.get("summary", "")

    try:
        content = truncate_html_words(content, conf.DEFAULT_ENTRY_WORD_LIMIT)
    except UnicodeDecodeError:
        content = ""

    return content


def date_to_datetime(field_name):
    """Given a post field, convert its :mod:`feedparser` date tuple to
    :class:`datetime.datetime` objects.

    :param field_name: The post field to use.

    """

    def _parsed_date_to_datetime(feed_obj, entry):
        """generated below"""
        if field_name in entry:
            try:
                time_ = time.mktime(entry[field_name])
                date = datetime.fromtimestamp(time_)
            except TypeError:
                date = datetime.now()
            return date
        return datetime.now()
    _parsed_date_to_datetime.__doc__ = \
            """Convert %s to :class:`datetime.datetime` object""" % field_name
    return _parsed_date_to_datetime
