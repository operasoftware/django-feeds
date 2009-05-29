import sys
import time
import feedparser
from datetime import datetime
from djangofeeds.models import Feed, Post, Enclosure, Category
from yadayada.db import TransactionContext
from django.utils.text import truncate_words, truncate_html_words
from httplib import OK as HTTP_OK
from httplib import MOVED_PERMANENTLY as HTTP_MOVED
from httplib import FOUND as HTTP_FOUND
from httplib import TEMPORARY_REDIRECT as HTTP_TEMPORARY_REDIRECT
from djangofeeds import logger as default_logger
from django.conf import settings

DEFAULT_POST_LIMIT = 20
DEFAULT_NUM_POSTS = -1
DEFAULT_CACHE_MIN = 30
DEFAULT_SUMMARY_MAX_WORDS = 25

STORE_ENCLOSURES = getattr(settings, "DJANGOFEEDS_STORE_ENCLOSURES", False)
STORE_CATEGORIES = getattr(settings, "DJANGOFEEDS_STORE_CATEGORIES", False)


def summarize(text, max_length=DEFAULT_SUMMARY_MAX_WORDS):
    return truncate_words(text, max_length)


def summarize_html(text, max_length=DEFAULT_SUMMARY_MAX_WORDS):
    return truncate_html_words(text, max_length)


def entries_by_date(entries, limit=-1):

    def date_entry_tuple(entry):
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


def _find_post_summary(feed_obj, entry):
    try:
        content = entry["content"][0]["value"]
    except (IndexError, KeyError):
        content = ""
    return summarize_html(entry.get("summary", content))


def _gen_parsed_date_to_datetime(field_name):

    def _parsed_date_to_datetime(feed_obj, entry):
        if field_name in entry:
            try:
                time_ = time.mktime(entry[field_name])
                date = datetime.fromtimestamp(time_)
            except TypeError:
                date = datetime.now()
            return date
        return datetime.now()
    return _parsed_date_to_datetime


def truncate_by_field(field, value):
    if isinstance(value, basestring) and \
            hasattr(field, "max_length") and value > field.max_length:
                return value[:field.max_length]
    return value


def truncate_field_data(model, data):
    fields = dict([(field.name, field) for field in model._meta.fields])
    return dict([(name, truncate_by_field(fields[name], value))
                    for name, value in data.items()])


class FeedImporter(object):
    parser = feedparser
    post_limit = DEFAULT_POST_LIMIT
    include_categories = STORE_CATEGORIES
    include_enclosures = STORE_ENCLOSURES
    update_on_import = True
    post_field_handlers = {
        "content": _find_post_summary,
        "date_published": _gen_parsed_date_to_datetime("published_parsed"),
        "date_updated": _gen_parsed_date_to_datetime("updated_parsed"),
        "link": lambda feed_obj, entry: entry.get("link") or feed_obj.feed_url,
        "feed": lambda feed_obj, entry: feed_obj,
        "guid": lambda feed_obj, entry: entry.get("guid", "").strip(),
        "title": lambda feed_obj, entry: entry.get("title",
                                                    "(no title)").strip(),
        "author": lambda feed_obj, entry: entry.get("author", "").strip(),
    }

    def __init__(self, **kwargs):
        self.post_limit = kwargs.get("post_limit", self.post_limit)
        self.update_on_import = kwargs.get("update_on_import",
                                            self.update_on_import)
        self.logger = kwargs.get("logger", default_logger)
        self.include_categories = kwargs.get("include_categories",
                                        self.include_categories)
        self.include_enclosures = kwargs.get("include_enclosures",
                                        self.include_enclosures)

    def import_feed(self, feed_url):
        logger = self.logger
        feed_url = feed_url.strip()
        logger.debug("Starting import of %s." % feed_url)
        feed = self.parser.parse(feed_url)
        logger.debug("%s parsed" % feed_url)
        # Feed can be local/fetched with a HTTP client.
        status = feed.get("status\n", HTTP_OK)

        if status == HTTP_FOUND or status == HTTP_MOVED:
            feed_url = feed.href

        feed_name = feed.channel.get("title", "(no title)").strip()
        feed_data = truncate_field_data(Feed, {
                        "sort": 0,
                        "name": feed_name,
                        "description": feed.channel.get("description", ""),
        })
        feed_obj, created = Feed.objects.get_or_create(feed_url=feed_url,
                                                       defaults=feed_data)
        logger.debug("%s Feed object created" % feed_url)
        if self.include_categories:
            feed_obj.categories.add(*self.get_categories(feed.channel))
            logger.debug("%s categories created" % feed_url)
        if self.update_on_import:
            logger.debug("%s Updating...." % feed_url)
            self.update_feed(feed_obj, feed=feed)
            logger.debug("%s Update finished!" % feed_url)
        return feed_obj

    def get_categories(self, obj):
        if hasattr(obj, "categories"):
            return [self.create_category(*cat)
                        for cat in obj.categories]
        return []

    def create_category(self, domain, name):
        domain = domain.strip()
        name = name.strip()
        fields = {"name": name, "domain": domain}
        cat, created = Category.objects.get_or_create(**fields)
        return cat

    def update_feed(self, feed_obj, feed=None):
        logger = self.logger
        limit = self.post_limit
        if not feed:
            self.logger.debug("uf: %s Feed was not provided, fetch..." % (
                feed_obj.feed_url))
            last_modified = None
            if feed_obj.http_last_modified:
                self.logger.debug("uf: %s Feed was last modified %s" % (
                        last_modified))
                last_modified = feed_obj.http_last_modified.timetuple()
            self.logger.debug("uf: Parsing feed %s" % feed_obj.feed_url)
            feed = self.parser.parse(feed_obj.feed_url,
                                     etag=feed_obj.http_etag,
                                     modified=last_modified)

        # If the document has been moved, update the unique feed_url,
        # to the new location.

        # Feed can be local/ not fetched with HTTP client.
        status = feed.get("status", HTTP_OK)
        self.logger.debug("uf: %s Feed HTTP status is %d" %
                (feed_obj.feed_url, status))


        if status == HTTP_FOUND or status == HTTP_MOVED:
            if feed_obj.feed_url != feed.href:
                feed_obj.feed_url = feed.href
            status = HTTP_OK

        if status == HTTP_OK or status == HTTP_TEMPORARY_REDIRECT:
            self.logger.debug("uf: %s Importing entries..." %
                    (feed_obj.feed_url))
            entries = [self.import_entry(entry, feed_obj)
                        for entry in entries_by_date(feed.entries, limit)]
            feed_obj.date_last_refresh = datetime.now()
            feed_obj.http_etag = feed.get("etag", "")
            if hasattr(feed, "modified"):
                feed_obj.http_last_modified = datetime.fromtimestamp(
                                                time.mktime(feed.modified))
            self.logger.debug("uf: %s Saving feed object..." %
                    (feed_obj.feed_url))
            feed_obj.save()
            return entries
        return []

    def create_enclosure(self, **kwargs):
        kwargs["length"] = kwargs.get("length", 0) or 0
        enclosure, created = Enclosure.objects.get_or_create(**kwargs)
        return enclosure

    def get_enclosures(self, entry):
        if not hasattr(entry, 'enclosures'):
            return []
            return [self.create_enclosure(url=enclosure.href,
                                        length=enclosure.length,
                                        type=enclosure.type)
                        for enclosure in entry.enclosures
                        if enclosure and hasattr(enclosure, "length")]

    def post_fields_parsed(self, entry, feed_obj):
        fields = [(key, handler(feed_obj, entry))
                        for key, handler in self.post_field_handlers.items()]
        return dict(fields)

    def import_entry(self, entry, feed_obj):
        self.logger.debug("ie: %s Importing entry..." % (feed_obj.feed_url))
        self.logger.debug("ie: %s parsing field data..." %
                (feed_obj.feed_url))
        fields = self.post_fields_parsed(entry, feed_obj)
        self.logger.debug("ie: %s Truncating field data..." %
                (feed_obj.feed_url))
        fields = truncate_field_data(Post, fields)

        if fields["guid"]:
            # Unique on GUID, feed
            self.logger.debug("ie: %s Is unique on GUID, storing post." % (
                feed_obj.feed_url))
            post, created = Post.objects.get_or_create(guid=fields["guid"],
                                                       feed=feed_obj,
                                                       defaults=fields)
        else:
            # Unique on title, feed
            self.logger.debug("ie: %s No GUID, storing post." % (
                feed_obj.feed_url))
            post, created = Post.objects.get_or_create(title=fields["title"],
                                                       feed=feed_obj,
                                                       defaults=fields)

        if not created:
            # Update post with new values (if any)
            self.logger.debug("ie: %s Feed not new, update values..." % (
                feed_obj.feed_url))
            post.save()

        if self.include_enclosures:
            self.logger.debug("ie: %s Saving enclosures..." % (
                feed_obj.feed_url))
            enclosures = self.get_enclosures(entry) or []
            post.enclosures.add(*enclosures)
        if self.include_categories:
            self.logger.debug("ie: %s Saving categories..." % (
                feed_obj.feed_url))
            categories = self.get_categories(entry) or []
            post.categories.add(*categories)

        self.logger.debug("ie: %s Post successfully imported..." % (
            feed_obj.feed_url))

        return post


def print_feed_summary(feed_obj):
    posts = feed_obj.get_posts()
    enclosures_count = sum([post.enclosures.count() for post in posts])
    categories_count = sum([post.categories.count() for post in posts]) \
                        + feed_obj.categories.count()
    sys.stderr.write("*** Total %d posts, %d categories, %d enclosures\n" % \
            (len(posts), categories_count, enclosures_count))


def refresh_all(verbose=True):
    """ Refresh all feeds in the system. """
    importer = FeedImporter()
    for feed_obj in Feed.objects.all():
        sys.stderr.write(">>> Refreshing feed %s...\n" % \
                (feed_obj.name))
        entries = importer.update_feed(feed_obj)

        if verbose:
            print_feed_summary(feed_obj)
