import sys
import time
import socket
import feedparser
import httplib as http
from datetime import datetime

from djangofeeds import conf
from djangofeeds import models
from djangofeeds import feedutil
from djangofeeds import exceptions
from djangofeeds.utils import get_default_logger, truncate_field_data


class FeedImporter(object):
    """Import/Update feeds.

    :keyword post_limit: See :attr`post_limit`.
    :keyword update_on_import: See :attr:`update_on_import`.
    :keyword logger: See :attr:`logger`.
    :keyword include_categories: See :attr:`include_categories`.
    :keyword include_enclosures: See :attr:`include_enclosures`.
    :keyword timeout: See :attr:`timeout`.

    .. attribute:: post_limit

        Default number of posts limit.

    .. attribute:: update_on_import

        By default, fetch new posts when a feed is imported

    .. attribute:: logger

       The :class:`logging.Logger` instance used for logging messages.

    .. attribute:: include_categories

        By default, include feed/post categories.

    .. attribute:: include_enclosures

        By default, include post enclosures.

    .. attribute:: timeout

        Default feed timeout.

    .. attribute:: parser

        The feed parser used. (Default: :mod:`feedparser`.)

    """
    parser = feedparser
    post_limit = conf.DEFAULT_POST_LIMIT
    include_categories = conf.STORE_CATEGORIES
    include_enclosures = conf.STORE_ENCLOSURES
    update_on_import = True
    post_model = models.Post
    feed_model = models.Feed
    category_model = models.Category
    enclosure_model = models.Enclosure
    post_field_handlers = {
        "content": feedutil.find_post_content,
        "date_published": feedutil.date_to_datetime("published_parsed"),
        "date_updated": feedutil.date_to_datetime("updated_parsed"),
        "link": lambda feed_obj, entry: entry.get("link") or feed_obj.feed_url,
        "feed": lambda feed_obj, entry: feed_obj,
        "guid": feedutil.get_entry_guid,
        "title": lambda feed_obj, entry: entry.get("title",
                                                    "(no title)").strip(),
        "author": lambda feed_obj, entry: entry.get("author", "").strip(),
    }

    def __init__(self, **kwargs):
        self.post_limit = kwargs.get("post_limit", self.post_limit)
        self.update_on_import = kwargs.get("update_on_import",
                                            self.update_on_import)
        self.logger = kwargs.get("logger", get_default_logger())
        self.include_categories = kwargs.get("include_categories",
                                        self.include_categories)
        self.include_enclosures = kwargs.get("include_enclosures",
                                        self.include_enclosures)
        self.timeout = kwargs.get("timeout", conf.FEED_TIMEOUT)

    def parse_feed(self, feed_url, etag=None, modified=None, timeout=None):
        """Parse feed using the current feed parser.

        :param feed_url: URL to the feed to parse.

        :keyword etag: E-tag recevied from last parse (if any).
        :keyword modified: ``Last-Modified`` HTTP header received from last
            parse (if any).
        :keyword timeout: Parser timeout in seconds.

        """
        prev_timeout = socket.getdefaulttimeout()
        timeout = timeout or self.timeout

        socket.setdefaulttimeout(timeout)
        try:
            feed = self.parser.parse(feed_url,
                                     etag=etag,
                                     modified=modified)

            alternate_links = feedutil.search_alternate_links(feed)
            # if there is not entries and we have some alternate links
            if not feed["entries"] and alternate_links:
                feed = self.parser.parse(alternate_links[0],
                                         etag=etag, modified=modified)
        finally:
            socket.setdefaulttimeout(prev_timeout)

        return feed

    def import_feed(self, feed_url, force=None, local=False):
        """Import feed.

        If feed is not seen before it will be created, otherwise
        just updated.

        :param feed_url: URL to the feed to import.
        :keyword force: Force import of feed even if it's been updated
            too recently.

        """
        logger = self.logger
        feed_url = feed_url.strip()
        feed = None
        try:
            feed_obj = self.feed_model.objects.get(feed_url=feed_url)
        except self.feed_model.DoesNotExist:
            try:
                feed = self.parse_feed(feed_url)
                # the feed URL could be modified at import because the parser
                # can follow a RSS alternate link in a web page.
                new_feed_url = feed.get("href", feed_url)
                # if it's the case, we need to try again with the new feed URL
                # because otherwise it would skip the
                # self.feed_model.DoesNotExist # check.
                if new_feed_url != feed_url:
                    return self.import_feed(new_feed_url, force, local)
            except socket.timeout:
                self.feed_model.objects.create(feed_url=feed_url, sort=0)
                raise exceptions.TimeoutError(
                        unicode(models.FEED_TIMEDOUT_ERROR_TEXT))
            except Exception:
                feed = {"status": 500}


            default_status = http.OK if local else http.NOT_FOUND

            status = feed.get("status", default_status)
            if status == http.NOT_FOUND:
                raise exceptions.FeedNotFoundError(
                        unicode(models.FEED_NOT_FOUND_ERROR_TEXT))
            if status not in models.ACCEPTED_STATUSES:
                raise exceptions.FeedCriticalError(
                        unicode(models.FEED_GENERIC_ERROR_TEXT),
                        status=status)

            # Feed can be local/fetched with a HTTP client.
            status = feed.get("status") or feed.get("status\n") or http.OK

            if status == http.FOUND or status == http.MOVED_PERMANENTLY:
                if feed_url != feed.href:
                    return self.import_feed(feed.href, force=force)

            feed_name = feed.channel.get("title", "(no title)").strip()
            feed_data = truncate_field_data(self.feed_model, {
                            "sort": 0,
                            "name": feed_name,
                            "description": feed.channel.get("description", ""),
            })
            feed_obj = self.feed_model.objects.update_or_create(
                                            feed_url=feed_url, **feed_data)

        if self.include_categories:
            feed_obj.categories.add(*self.get_categories(feed.channel))

        if self.update_on_import:
            feed_obj = self.update_feed(feed_obj, feed=feed, force=force)

        return feed_obj

    def get_categories(self, obj):
        """Get and save categories."""
        return [self.create_category(*cat)
                    for cat in getattr(obj, "categories", [])]

    def create_category(self, domain, name):
        """Create new category.

        :param domain: The category domain.
        :param name: The name of the category.

        """
        return self.category_model.objects.update_or_create(
                      name=name.strip(),
                      domain=domain and domain.strip() or "")

    def update_feed(self, feed_obj, feed=None, force=False):
        """Update (refresh) feed.

        The feed must already exist in the system, if not you have
        to import it using :meth:`import_feed`.

        :param feed_obj: the Feed object
        :keyword feed: If feed has already been parsed you can pass the
            structure returned by the parser so it doesn't have to be parsed
            twice.
        :keyword force: Force refresh of the feed even if it has been
            recently refreshed already.

        """
        already_fresh = (feed_obj.date_last_refresh and
                         datetime.now() < feed_obj.date_last_refresh +
                         conf.MIN_REFRESH_INTERVAL)

        if already_fresh and not force:
            self.logger.info(
                    "Feed %s is fresh. Skipping refresh." % feed_obj.feed_url)
            return feed_obj

        limit = self.post_limit
        if not feed:
            last_modified = None
            if feed_obj.http_last_modified and not force:
                last_modified = feed_obj.http_last_modified.timetuple()
            etag = feed_obj.http_etag if not force else None

            try:
                feed = self.parse_feed(feed_obj.feed_url,
                                       etag=etag,
                                       modified=last_modified)
            except socket.timeout:
                return feed_obj.save_timeout_error()
            except Exception, e:
                return feed_obj.save_generic_error()

        # Feed can be local/ not fetched with HTTP client.
        status = feed.get("status", http.OK)
        if status == http.NOT_MODIFIED and not force:
            return feed_obj

        if feed_obj.is_error_status(status):
            return feed_obj.set_error_status(status)

        if feed.entries:
            sorted_by_date = feedutil.entries_by_date(feed.entries, limit)

            entries = [self.import_entry(entry, feed_obj)
                            for entry in sorted_by_date]

        feed_obj.date_last_refresh = datetime.now()
        feed_obj.http_etag = feed.get("etag", "")
        if hasattr(feed, "modified") and feed.modified:
            try:
                as_ts = time.mktime(feed.modified)
                feed_obj.http_last_modified = datetime.fromtimestamp(as_ts)
            except TypeError:
                pass

        self.logger.debug("uf: %s Saving feed object..." % (
                            feed_obj.feed_url))

        feed_obj.save()
        return feed_obj

    def create_enclosure(self, **kwargs):
        """Create new enclosure."""
        kwargs.setdefault("length", 0)
        return self.enclosure_model.objects.update_or_create(**kwargs)

    def get_enclosures(self, entry):
        """Get and create enclosures for feed."""
        return [self.create_enclosure(url=enclosure.href,
                                    length=enclosure.length,
                                    type=enclosure.type)
                    for enclosure in getattr(entry, "enclosures", [])
                        if enclosure and hasattr(enclosure, "length")]

    def post_fields_parsed(self, entry, feed_obj):
        """Parse post fields."""
        return dict((key, handler(feed_obj, entry))
                        for key, handler in self.post_field_handlers.items())

    def import_entry(self, entry, feed_obj):
        """Import feed post entry."""
        self.logger.debug("ie: %s Importing entry..." % feed_obj.feed_url)

        fields = self.post_fields_parsed(entry, feed_obj)
        post = self.post_model.objects.update_post(feed_obj, **fields)

        if self.include_enclosures:
            post.enclosures.add(*(self.get_enclosures(entry) or []))
        if self.include_categories:
            post.categories.add(*(self.get_categories(entry) or []))

        self.logger.debug("ie: %s Post successfully imported..." % (
            feed_obj.feed_url))

        return post
