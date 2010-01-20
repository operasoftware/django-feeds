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

    def update_or_create(self, **kwargs):
        try:
            obj = super(PostManager, self).update_or_create(**kwargs)
        except self.model.MultipleObjectsReturned:
            guid = kwargs.get("guid")
            feed = kwargs.get("feed")
            if guid:
                self.filter(guid=guid, feed=feed).delete()
                obj, created = self.get_or_create(**kwargs)
            else:
                raise

        return obj

    def update_post(self, feed_obj, **fields):
        fields = truncate_field_data(self.model, fields)
        # posts entry with no valid dates will recieve a new
        # different date every time and be updated. That's
        # not what we want. Besides, what do we need to update here?
        # A change in the title, or link will create a new GUID
        try:
            post = self.get(guid=fields["guid"], feed=feed_obj)
            # TODO: Update some field here
        except self.model.DoesNotExist:
            post = self.create(guid=fields["guid"], feed=feed_obj,
                                     defaults=fields)
