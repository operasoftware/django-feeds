from django.db import models
from yadayada.managers import StdManager

DEFAULT_POST_LIMIT = 5


class FeedManager(StdManager):
    """Manager class for Feeds"""
    pass


class PostManager(models.Manager):
    """Manager class for Posts"""

    def all_by_order(self, limit=DEFAULT_POST_LIMIT):
        ordering = self.model._meta.ordering
        return self.all().order_by(*ordering)[:limit]
