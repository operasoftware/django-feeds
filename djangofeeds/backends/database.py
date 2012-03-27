from djangofeeds.models import Post


class DatabaseBackend(object):

    def get_post_model(self):
        return Post

    def all_posts_by_order(self, feed, **kwargs):
        return feed.post_set.order_by("-date_published")

    def get_post_count(self, feed):
        return feed.post_set.count()
