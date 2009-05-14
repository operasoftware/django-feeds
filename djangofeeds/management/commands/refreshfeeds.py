from __future__ import with_statement
from yadayada.db import TransactionContext
from yadayada.models import Language
from django.core.management.base import CommandError, NoArgsCommand
from django.conf import settings
from django.core import exceptions
from djangofeeds.importers import refresh_all
from djangofeeds.messaging import refresh_all_feeds_delayed
from optparse import make_option


def refresh_all_feeds():
    with TransactionContext():
        refresh_all()

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--lazy', '-l', action="store_true", dest="lazy",
                    default=False, help="Delay the actual importing to AMQP"),
        make_option('--file', '-f', action="store", dest="file",
                    help="Import all feeds from a file with feed URLs "
                    "seperated by newline."),
    )

    help = ("Refresh feeds")

    requires_model_validation = True
    can_import_settings = True

    def handle_noargs(self, **options):
        lazy = options.get("lazy")
        work = options.get("work")
        from_file = options.get("file")
        concurrency = options.get("concurrency")
        if from_file:
            refresh_all_feeds_delayed(from_file=from_file)
        elif lazy:
            refresh_all_feeds_delayed()
        else:
            refresh_all_feeds()

