"""Model working with Feeds and Posts."""
import httplib as http
from datetime import datetime, timedelta

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.utils.hashcompat import md5_constructor

from celery.utils import timedelta_seconds

from djangofeeds import conf
from djangofeeds.utils import naturaldate
from djangofeeds.managers import FeedManager, PostManager
from djangofeeds.managers import EnclosureManager, CategoryManager
from djangofeeds.backends import default_post_backend

ACCEPTED_STATUSES = frozenset([http.OK,
                               http.FOUND,
                               http.NOT_MODIFIED,
                               http.MOVED_PERMANENTLY,
                               http.TEMPORARY_REDIRECT])

FEED_TIMEDOUT_ERROR = "TIMEDOUT_ERROR"
FEED_NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
FEED_GENERIC_ERROR = "GENERIC_ERROR"

FEED_TIMEDOUT_ERROR_TEXT = _(
    u"The feed does not seem to be respond. We will try again later.")
FEED_NOT_FOUND_ERROR_TEXT = _(
    u"You entered an incorrect URL or the feed you requested does not exist "
    u"anymore.")
FEED_GENERIC_ERROR_TEXT = _(
    u"There was a problem with the feed you provided, please check the URL "
    u"for mispellings or try again later.")

FEED_ERROR_CHOICES = (
        (FEED_TIMEDOUT_ERROR, FEED_TIMEDOUT_ERROR_TEXT),
        (FEED_NOT_FOUND_ERROR, FEED_NOT_FOUND_ERROR_TEXT),
        (FEED_GENERIC_ERROR, FEED_GENERIC_ERROR_TEXT),
)


class Category(models.Model):
    """Category associated with :class:`Post`` or :class:`Feed`.

    .. attribute:: name

        Name of the category.

    .. attribute:: domain

        The type of category

    """
    name = models.CharField(_(u"name"), max_length=128)
    domain = models.CharField(_(u"domain"),
                              max_length=128, null=True, blank=True)

    objects = CategoryManager()

    class Meta:
        unique_together = ("name", "domain")
        verbose_name = _(u"category")
        verbose_name_plural = _(u"categories")

    def __unicode__(self):
        if self.domain:
            return u"%s [%s]" % (self.name, self.domain)
        return u"%s" % self.name


class Feed(models.Model):
    """An RSS feed

    .. attribute:: name

        The name of the feed.

    .. attribute:: feed_url

        The URL the feed is located at.

    .. attribute:: description

        The feeds description in full text/HTML.

    .. attribute:: link

        The link the feed says it's located at.
        Can be different from :attr:`feed_url` as it's the
        source we got from the user.

    .. attribute:: date_last_refresh

        Date of the last time this feed was refreshed.

    .. attribute:: last_error

        The last error message (if any).

    .. attribute:: ratio

        The apparent importance of this feed.

    """
    supports_categories = False
    supports_enclosures = False

    name = models.CharField(_(u"name"), max_length=200)
    feed_url = models.URLField(_(u"feed URL"), unique=True)
    description = models.TextField(_(u"description"))
    link = models.URLField(_(u"link"), max_length=200, blank=True)
    http_etag = models.CharField(_(u"E-Tag"),
                                 editable=False, blank=True,
                                 null=True, max_length=200)
    http_last_modified = models.DateTimeField(_(u"Last-Modified"), null=True,
                                              editable=False, blank=True)
    date_last_refresh = models.DateTimeField(_(u"date of last refresh"),
                                        null=True, blank=True, editable=False)
    categories = models.ManyToManyField(Category)
    last_error = models.CharField(_(u"last error"), blank=True, default="",
                                 max_length=32, choices=FEED_ERROR_CHOICES)
    ratio = models.FloatField(default=0.0)
    sort = models.SmallIntegerField(_(u"sort order"), default=0)
    date_created = models.DateTimeField(_(u"date created"), auto_now_add=True)
    date_changed = models.DateTimeField(_(u"date changed"), auto_now=True)
    date_last_requested = models.DateTimeField(_(u"last requested"),
                                               auto_now_add=True)
    is_active = models.BooleanField(_(u"is active"), default=True)
    freq = models.IntegerField(_(u"frequency"), default=conf.REFRESH_EVERY)

    objects = FeedManager()

    class Meta:
        ordering = ("id", )
        verbose_name = _(u"syndication feed")
        verbose_name_plural = _(u"syndication feeds")

    def __init__(self, *args, **kwargs):
        super(Feed, self).__init__(*args, **kwargs)
        self.poststore = default_post_backend()

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.feed_url)

    def get_posts(self, **kwargs):
        """Get all :class:`Post`s for this :class:`Feed` in order."""
        return self.poststore.all_posts_by_order(self)

    def get_post_count(self):
        return self.poststore.get_post_count(self)

    def frequencies(self, limit=None, order="-date_updated"):
        posts = self.post_set.values("date_updated").order_by(order)[0:limit]
        return [posts[i - 1]["date_updated"] - post["date_updated"]
                    for i, post in enumerate(posts)
                        if i]

    def average_frequency(self, limit=None, min=5,
            default=timedelta(hours=2)):
        freqs = self.frequencies(limit=limit)
        if len(freqs) < min:
            return default
        average = sum(map(timedelta_seconds, freqs)) / len(freqs)
        return timedelta(seconds=average)

    def update_frequency(self, limit=None, min=5, save=True):
        self.freq = timedelta_seconds(self.average_frequency(limit, min))
        save and self.save()

    def expire_old_posts(self, max_posts=100, commit=False):
        """Expire old posts.

        :keyword max_posts: The maximum number of posts to keep for a feed.
            We keep this value high to avoid incessant delete on feed that
            have a lot of posts.
        :keyword commit: Commit the transaction, set to ``False`` if you want
            to manually handle the transaction.

        :returns: The number of messages deleted.

        """
        by_date = self.post_set.order_by("-date_published")
        expired_posts = [post["id"]
                            for post in by_date.values("id")[max_posts:]]
        if expired_posts:
            Post.objects.filter(pk__in=expired_posts).delete()
            return len(expired_posts)
        return 0

    def is_error_status(self, status):
        return status == http.NOT_FOUND or status not in ACCEPTED_STATUSES

    def error_for_status(self, status):
        if status == http.NOT_FOUND:
            return FEED_NOT_FOUND_ERROR
        if status not in ACCEPTED_STATUSES:
            return FEED_GENERIC_ERROR

    def save_error(self, error_msg):
        self._set_last_error = True
        self.last_error = error_msg
        self.save()
        return self

    def save_generic_error(self):
        return self.save_error(FEED_GENERIC_ERROR)

    def save_timeout_error(self):
        return self.save_error(FEED_TIMEDOUT_ERROR)

    def set_error_status(self, status):
        return self.save_error(self.error_for_status(status))

    @property
    def date_last_refresh_naturaldate(self):
        return unicode(naturaldate(self.date_last_refresh))


def sig_reset_last_error(sender, instance, **kwargs):
    if not instance._set_last_error:
        instance.last_error = u""
signals.pre_save.connect(sig_reset_last_error, sender=Feed)


def sig_init_feed_set_last_error(sender, instance, **kwargs):
    instance._set_last_error = False
signals.post_init.connect(sig_init_feed_set_last_error, sender=Feed)


class Enclosure(models.Model):
    """Media enclosure for a Post

    .. attribute:: url

        The location of the media attachment.

    .. attribute:: type

        The mime/type of the attachment.

    .. attribute:: length

        The actual content length of the file
        pointed to at :attr:`url`.

    """
    url = models.URLField(_(u"URL"))
    type = models.CharField(_(u"type"), max_length=200)
    length = models.PositiveIntegerField(_(u"length"), default=0)

    objects = EnclosureManager()

    class Meta:
        verbose_name = _(u"enclosure")
        verbose_name_plural = _(u"enclosures")

    def __unicode__(self):
        return u"%s %s (%d)" % (self.url, self.type, self.length)


class Post(models.Model):
    """A Post for an RSS feed

    .. attribute:: feed

        The feed which this is a post for.

    .. attribute:: title

        The title of the post.

    .. attribute:: link

        Link to the original article.

    .. attribute:: content

        The posts content in full-text/HTML.

    .. attribute:: guid

        The GUID for this post (unique for :class:`Feed`)

    .. attribute:: author

        Name of this posts author.

    .. attribute:: date_published

        The date this post was published.

    .. attribute:: date_updated

        The date this post was last changed/updated.

    .. attribute:: enclosures

        List of media attachments for this post.

    """

    feed = models.ForeignKey(Feed, null=False, blank=False)
    title = models.CharField(_(u"title"), max_length=200)
    link = models.URLField(_(u"link"))
    content = models.TextField(_(u"content"), blank=True)
    guid = models.CharField(_(u"guid"), max_length=200, blank=True)
    author = models.CharField(_(u"author"), max_length=50, blank=True)
    date_published = models.DateField(_(u"date published"))
    date_updated = models.DateTimeField(_(u"date updated"))
    enclosures = models.ManyToManyField(Enclosure, blank=True)
    categories = models.ManyToManyField(Category)

    objects = PostManager()

    class Meta:
        # sorting on anything else than id is catastrophic for
        # performance
        # even an ordering by id is not smart
        # ordering = ["-id"]
        verbose_name = _(u"post")
        verbose_name_plural = _(u"posts")

    def auto_guid(self):
        """Automatically generate a new guid from the metadata available."""
        return md5_constructor("|".join((
                    self.title, self.link, self.author))).hexdigest()

    def __unicode__(self):
        return u"%s" % self.title

    @property
    def date_published_naturaldate(self):
        date = self.date_published
        as_datetime = datetime(date.year, date.month, date.day)
        return unicode(naturaldate(as_datetime))

    @property
    def date_updated_naturaldate(self):
        return unicode(naturaldate(self.date_updated))
