from redish.model import Model, Manager
from redish.utils import maybe_datetime


class Entry(Model):

    def post_save(self):
        self.guid_map[self.guid] = self.id
        self.sort_index.add(self.id, maybe_datetime(self.timestamp))

    def post_delete(self):
        self.sort_index.remove(self.id)
        del(self.guid_map[self.guid])

    @property
    def sort_index(self):
        return self.objects.get_sort_index(self.feed_url)

    @propery
    def guid_map(self):
        return self.objects.get_guid_map(self.feed_url)


class Entries(Manager):
    db = "djangofeeds"
    model = Entry

    def all_by_order(self, feed_url, limit=20):
        for id in self.get_sort_index(feed_url)[:limit]:
            yield self[id]

    def update_or_create(self, feed_url, **fields):
        try:
            entry = self.get_by_guid(feed_url, fields["guid"])
            entry.update(fields)
            entry.save()
            return entry
        except KeyError:
            return self.create(**fields)

    def get_by_guid(self, feed_url, guid):
        return self.get(self.get_guid_map(feed_url)[guid])

    def get_sort_index(self, feed_url):
        return self.SortedSet((feed_url, "sort"))

    def get_guid_map(self, feed_url):
        return self.Hash((feed_url, "guidmap"))


if __name__ == "__main__":
    from datetime import datetime
    posts = Entries(host="localhost")

    feed1 = dict(feed_url="http://rss.com/example",
                 title="Example Post",
                 guid="http://rss.com/example/1",
                 link="http://rss.com/example/1",
                 content="This is an example",
                 timestamp=datetime.now())
    entry = posts.Entry(**data)
    entry_id = entry.save()
    assert entry_id == entry.id

    stored = posts.get(entry_id)
    stored.content = "Content has been changed"
    entry_id = stored.save()
    assert stored.id == new_id)
    again = posts.get(entry_id)

    stored.delete()

    feed2 = posts.create(**data)

    for post in iter(posts):
        print("(%s) %s" % (post.id, post.title))

