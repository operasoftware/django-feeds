import sys
from datetime import timedelta, datetime

from django.db import models
from django.db.models.query import QuerySet

from djangofeeds.utils import truncate_field_data

DEFAULT_POST_LIMIT = 5


def update_with_dict(obj, fields):
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
        threshold = datetime.now() - timedelta(seconds=interval)
        return self.filter(date_last_refresh__lt=threshold)


class ExtendedManager(models.Manager):

    def get_query_set(self):
        return ExtendedQuerySet(self.model)

    def update_or_create(self, **kwargs):
        return self.get_query_set().update_or_create(**kwargs)


FeedManager = ExtendedManager
CategoryManager = ExtendedManager
EnclosureManager = ExtendedManager


class FeedManager(ExtendedManager):

    def ratio(self, min=None, max=None):
        query = {}
        if min is not None:
            query["ratio__gt"] = min
        if max is not None:
            query["ratio__lt"] = max
        return self.filter(**query)


class PostManager(ExtendedManager):
    """Manager class for Posts"""

    def all_by_order(self, limit=DEFAULT_POST_LIMIT):
        ordering = self.model._meta.ordering
        return self.all().order_by(*ordering)[:limit]

    def update_post(self, feed_obj, **fields):
        return self.update_or_create(guid=fields["guid"], feed=feed_obj,
                        defaults=truncate_field_data(self.model, fields))
