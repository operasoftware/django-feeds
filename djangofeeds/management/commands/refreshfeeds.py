from __future__ import with_statement

import sys
from optparse import make_option

from yadayada.db import TransactionContext
from yadayada.models import Language

from django.conf import settings
from django.core import exceptions
from django.core.management.base import CommandError, NoArgsCommand

from djangofeeds.tasks import refresh_feed
from djangofeeds.models import Feed
from djangofeeds.importers import refresh_all


def refresh_all_feeds_delayed(from_file=None):
    urls = (feed.feed_url for feed in Feed.objects.all())
    if from_file is not None:
        with file(from_file) as feedfile:
            urls = iter(feedfile.readlines())

    map(refresh_feed.delay, urls)


def refresh_all_feeds():
    with TransactionContext():
        refresh_all()


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--lazy', '-l', action="store_true", dest="lazy",
                    default=False, help="Delay the actual importing to celery"),
        make_option('--file', '-f', action="store", dest="file",
                    help="Import all feeds from a file with feed URLs "
                    "seperated by newline."),
    )

    help = ("Refresh feeds", )

    requires_model_validation = True
    can_import_settings = True

    def handle_noargs(self, **options):
        lazy = options.get("lazy")
        from_file = options.get("file")
        if from_file or lazy:
            refresh_all_feeds_delayed(from_file)
        else:
            refresh_all_feeds()
