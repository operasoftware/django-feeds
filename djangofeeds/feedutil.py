from djangofeeds.text import summarize, summarize_html
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


def find_post_summary(feed_obj, entry):
    """Find the correct summary field for a post."""
    try:
        content = entry["content"][0]["value"]
    except (IndexError, KeyError):
        content = ""

    def summarize_force(content):
        return content[:conf.DEFAULT_SUMMARY_MAX_WORDS * 10]

    content = entry.get("summary", content)
    for summarize_fun in (summarize_html, summarize):
        try:
            return summarize_fun(content)
        except UnicodeDecodeError:
            pass

    return summarize_force(content)


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
