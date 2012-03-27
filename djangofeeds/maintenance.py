from django.db import transaction

from djangofeeds.models import Feed


@transaction.commit_manually
def expire_posts(min_posts=20, commit_every=10000):
    """Expire old posts for all feeds in the system.

    :keyword min_posts: Maximum number of posts to keep in a feed.
        Default is 20.
    :keyword commit_every: Commit transaction every ``n`` posts.
        Default is 10,000.

    """
    total = 0
    for feed in Feed.objects.all():
        print("Expiring posts for %s" % feed.feed_url)
        try:
            deleted = feed.expire_old_posts(min_posts=min_posts)
        except BaseException:
            transaction.rollback()
        else:
            total += deleted
            if not total % commit_every:
                transaction.commit()
