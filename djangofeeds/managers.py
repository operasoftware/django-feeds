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


class ExtendedManager(models.Manager):

    def get_query_set(self):
        return ExtendedQuerySet(self.model)

    def update_or_create(self, **kwargs):
        return self.get_query_set().update_or_create(**kwargs)


FeedManager = ExtendedManager
CategoryManager = ExtendedManager
EnclosureManager = ExtendedManager


class PostManager(ExtendedManager):
    """Manager class for Posts"""

    def all_by_order(self, limit=DEFAULT_POST_LIMIT):
        ordering = self.model._meta.ordering
        return self.all().order_by(*ordering)[:limit]

    def update_post(self, feed_obj, **fields):
        fields = truncate_field_data(self.model, fields)

        if fields.get("guid"):
            # Unique on guid, feed
            post = self.update_or_create(guid=fields["guid"], feed=feed_obj,
                                         defaults=fields)
        else:
            # Unique on title, feed, date_published
            lookup_fields = dict(date_published=fields["date_published"],
                                 title=fields["title"],
                                 feed=feed_obj)
            try:
                return self.update_or_create(defaults=fields, **lookup_fields)
            except self.model.MultipleObjectsReturned:
                dupe = self._find_duplicate_post(lookup_fields, fields)
                if dupe:
                    return update_with_dict(dupe, fields)
                else:
                    return self.create(**fields)
