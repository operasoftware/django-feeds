"""Model working with Feeds and Posts.

Model Classes
-------------

.. class:: Category
        
    :class:`Category` associated with :class:`Post` or :class:`Feed`.

.. class:: Feed
        
    Model representing a feed.

.. class:: Enclosure

    Model representing media attached to a :class:`Post`.

.. class:: Post

    Model representing a single post in a :class:`Feed`.


portal-dev@list.opera.com
Copyright (c) 2009 Opera Software ASA.

"""

from django.db import models
from yadayada.models import StdModel
from tagging.models import Tag
from djangofeeds.managers import FeedManager, PostManager
from django.utils.translation import ugettext_lazy as _

__all__ = ["Feed", "Enclosure", "Post", "Category"]

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
    domain = models.CharField(_(u"domain"), max_length=128, null=True,
                                                            blank=True)

    class Meta:
        unique_together = ("name", "domain")
        verbose_name = _(u"category")
        verbose_name_plural = _(u"categories")

    def __unicode__(self):
        if self.domain:
            return u"%s [%s]" % (self.name, self.domain)
        return u"%s" % self.name


class Feed(StdModel):
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

    """

    name = models.CharField(_(u"name"), max_length=200)
    feed_url = models.URLField(_(u"feed URL"), unique=True)
    description = models.TextField(_(u"description"))
    link = models.URLField(_(u"link"), max_length=200, blank=True)
    http_etag = models.CharField(_(u"E-Tag"), editable=False, blank=True,
                                                              null=True,
                                                              max_length=200),
    http_last_modified = models.DateTimeField(_(u"Last-Modified"),
                                                               null=True,
                                                               editable=False,
                                                               blank=True)
    date_last_refresh = models.DateTimeField(_(u"date of last refresh"),
                                        null=True, blank=True, editable=False)
    categories = models.ManyToManyField(Category)
    last_error = models.CharField(_(u"last error"), blank=True, default="",
                                 max_length=32, choices=FEED_ERROR_CHOICES)

    objects = FeedManager()

    class Meta:
        ordering = ['name', 'feed_url']
        verbose_name = _(u"syndication feed")
        verbose_name_plural = _(u"syndication feeds")

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.feed_url)

    def get_posts(self, **kwargs):
        """Get all :class:`Post`s for this :class:`Feed` in order."""
        return self.post_set.all_by_order(**kwargs)


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
        ordering = ['-date_updated', 'date_published']
        verbose_name = _(u"post")
        verbose_name_plural = _(u"posts")

    def __unicode__(self):
        return u"%s" % self.title
