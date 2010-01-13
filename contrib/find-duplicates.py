import djangolets
djangolets.entrypoint()

from django.db import transaction

from djangolets.mapred import QuerySetMapper, Reducer

from djangofeeds.models import Feed


def Feeds(reducer, start=None, stop=None):
    return QuerySetMapper(reducer, Feed.objects.all(), start, stop)


class DuplicateReducer(Reducer):

    def iterduplicates(self, feed):
        seen = set()
        for post in reversed(feed.post_set.all_by_order(limit=None)):
            uid = hash(post)
            if uid in seen:
                yield post
            else:
                seen.add(uid)

    def process(self, feed):
        return self.iterduplicates(feed)


def duplicate_posts():
    for duplicates in Feeds(DuplicateReducer()):
        for post in duplicates:
            yield post


@transaction.commit_manually
def delete_duplicates(commit_every=1000):
    try:
        for i, post in enumerate(duplicate_posts()):
            print("Duplicate post: %s (%s)" % (post.feed.name.encode("utf-8"),
                                               post.title.encode("utf-8")))
            post.delete()
            if not i % commit_every:
                transaction.commit()
    except BaseException:
        transaction.rollback()


if __name__ == "__main__":
    delete_duplicates()
