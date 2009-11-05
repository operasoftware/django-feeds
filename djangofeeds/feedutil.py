from django.utils.text import truncate_html_words
from djangofeeds import conf
from datetime import datetime
import time


def entries_by_date(entries, limit=-1):
    """Sort the feed entries by date

    :param entries: Entries given from :mod:`feedparser``.
    :param limit: Limit number of posts.

    """

    def date_entry_tuple(entry):
        """Find the most current date entry tuple."""
        if "date_parsed" in entry:
            return (entry["date_parsed"], entry)
        if "updated_parsed" in entry:
            return (entry["updated_parsed"], entry)
        if "published_parsed" in entry:
            return (entry["published_parsed"], entry)
        return (time.localtime(), entry)

    sorted_entries = [date_entry_tuple(entry)
                            for entry in entries]
    sorted_entries.sort()
    sorted_entries.reverse()
    return [entry for (date, entry) in sorted_entries[:limit]]


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
