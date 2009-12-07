from django.utils.text import truncate_html_words
from djangofeeds import conf
from datetime import datetime
from djangofeeds.optimization import BeaconDetector
import time
from datetime import datetime, timedelta

_beacon_detector = BeaconDetector()


def entries_by_date(entries, limit=None):
    """Sort the feed entries by date

    :param entries: Entries given from :mod:`feedparser``.
    :param limit: Limit number of posts.

    """
    def date_entry_tuple(entry, counter):
        """Find the most current date entry tuple."""
        if "date_parsed" in entry:
            return (entry["date_parsed"], entry)
        if "updated_parsed" in entry:
            return (entry["updated_parsed"], entry)
        if "published_parsed" in entry:
            return (entry["published_parsed"], entry)
        return (now - timedelta(seconds = (counter * 30)), entry)

    sorted_entries = []
    counter = 0
    now = datetime.now()
    for entry in entries:
        sorted_entries.append(date_entry_tuple(entry, counter))
        counter += 1

    sorted_entries.sort()
    sorted_entries.reverse()
    if limit:
        return [entry for (date, entry) in sorted_entries[:limit]]
    else:
        return [entry for (date, entry) in sorted_entries]


def find_post_content(feed_obj, entry):
    """Find the correct content field for a post."""
    try:
        content = entry["content"][0]["value"]
    except (IndexError, KeyError):
        content = entry.get("description") or entry.get("summary", "")

    try:
        #content = _beacon_detector.stripsafe(content)
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
