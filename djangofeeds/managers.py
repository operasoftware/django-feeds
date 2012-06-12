import pytz
from datetime import timedelta, datetime

from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import MultipleObjectsReturned

from djangofeeds.utils import truncate_field_data

""" .. data:: DEFAULT_POST_LIMIT

    The default limit of number of posts to keep in a feed.
    Default is 5 posts.

"""
DEFAULT_POST_LIMIT = 25


def update_with_dict(obj, fields):
    """Update and save a model from the values of a :class:`dict`."""
    set_value = lambda (name, val): setattr(obj, name, val)
    map(set_value, fields.items())
    obj.save()
    return obj


class ExtendedQuerySet(QuerySet):

    def update_or_create(self, **kwargs):
        obj, created = self.get_or_create(**kwargs)

        if not created:
            fields = dict(kwargs.pop("defaults", {}))
            fields.update(kwargs)
            update_with_dict(obj, fields)

        return obj

    def since(self, interval):
        """Return all the feeds refreshed since a specified
        amount of seconds."""
        threshold = datetime.now(pytz.utc) - timedelta(seconds=interval)
        return self.filter(date_last_refresh__lt=threshold)

    def ratio(self, min=None, max=None):
        """Select feeds based on ratio.

        :param min: Don't include feeds with a ratio lower than this.
        :param max: Don't include feeds with a ratio higher than this.

        """
        query = {}
        if min is not None:
            query["ratio__gt"] = min
        if max is not None:
            query["ratio__lt"] = max
        return self.filter(**query)

    def frequency(self, min=None, max=None):
        """Select feeds based on update frequency.

        :param min: Don't include feeds with a frequency lower than this.
        :param max: Don't include feeds with a frequency higher than this.

        """
        query = {}
        if min is not None:
            query["freq__gt"] = min
        if max is not None:
            query["freq__lt"] = max
        return self.filter(**query)


class ExtendedManager(models.Manager):
    """Manager supporting :meth:`update_or_create`."""

    def get_query_set(self):
        return ExtendedQuerySet(self.model)

    def update_or_create(self, **kwargs):
        return self.get_query_set().update_or_create(**kwargs)


class FeedManager(ExtendedManager):
    """Manager for :class:`djangofeeds.models.Feed`."""

    def since(self, interval):
        return self.get_query_set().since(interval)

    def ratio(self, *args, **kwargs):
        return self.get_query_set().ratio(*args, **kwargs)

    def frequency(self, *args, **kwargs):
        return self.get_query_set().frequency(*args, **kwargs)


class PostManager(ExtendedManager):
    """Manager class for Posts"""

    def all_by_order(self, limit=DEFAULT_POST_LIMIT):
        """Get feeds using the default sort order."""
        ordering = self.model._meta.ordering
        return self.all().order_by(*ordering)[:limit]

    def update_or_create(self, feed_obj, **fields):
        """Update post with new values."""
        super_update = super(PostManager, self).update_or_create
        defaults = truncate_field_data(self.model, fields)
        try:
            return super_update(guid=defaults["guid"], feed=feed_obj,
                                         defaults=defaults)
        except MultipleObjectsReturned:
            self.filter(guid=defaults["guid"], feed=feed_obj).delete()
            super_update(guid=defaults["guid"], feed=feed_obj,
                         defaults=defaults)


class CategoryManager(ExtendedManager):
    pass


class EnclosureManager(ExtendedManager):
    pass
