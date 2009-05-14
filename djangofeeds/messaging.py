import sys
import djangofeeds.tasks
from celery.task import delay_task
from djangofeeds.models import Feed


def delay_feed(feed_url):
    sys.stderr.write(
        ">>> Sending message to broker: Refresh feed %s\n" % feed_url)
    delay_task("djangofeeds.refresh_feed", feed_url=feed_url)


def refresh_all_feeds_delayed(from_file=None):
    if from_file:
        feed_urls = file(from_file).readlines()
        for feed_url in feed_urls:
            delay_feed(feed_url)
    for feed_obj in Feed.objects.all():
        delay_feed(feed_obj.feed_url)
