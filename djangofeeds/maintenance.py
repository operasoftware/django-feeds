from djangofeeds.models import Feed, Post
from datetime import datetime, timedelta


def expire_posts(min_posts=20):

    for feed in Feed.objects.all():
        print("Expiring posts for %s" % feed.feed_url)
        feed.expire_old_posts(min_posts=min_posts)
