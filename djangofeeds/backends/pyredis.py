from redish.utils import maybe_datetime
from redish.models import Model, Manager

from djangofeeds import conf
from djangofeeds.managers import DEFAULT_POST_LIMIT


class Entry(Model):

    def post_save(self):
        self.sort_index.add(self.id, maybe_datetime(self.timestamp))
        self.guid_map[self.guid] = self.id

    def post_delete(self):
        del(self.guid_map[self.guid])
        self.sort_index.remove(self.id)

    @property
    def sort_index(self):
        return self.objects.get_sort_index(self["feed_url"])

    @property
    def guid_map(self):
        return self.objects.get_guid_map(self["feed_url"])

    def __repr__(self):
        if "guid" in self and "title" in self:
            return "<Entry: %s '%s'>" % (self.guid, self.title)
        return super(Entry, self).__repr__()


class Entries(Manager):
    db = "djangofeeds"
    model = Entry

    def all_by_order(self, feed_url, limit=DEFAULT_POST_LIMIT):
        return map(self.get, self.get_sort_index(feed_url).revrange(0, limit))

    def update_or_create(self, feed_obj, **fields):
        fields["feed_url"] = feed_obj.feed_url
        fields["timestamp"] = fields["date_updated"]
        try:
            entry = self.get_by_guid(fields["feed_url"], fields["guid"])
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
        return self.Dict((feed_url, "guidmap"))


class RedisBackend(object):
    _entry = None

    def get_post_model(self):
        return Entries(host=conf.REDIS_POST_HOST,
                       port=conf.REDIS_POST_PORT,
                       db=conf.REDIS_POST_DB).Entry()

    def all_posts_by_order(self, feed, **kwargs):
        return self.Entry.objects.all_by_order(feed.feed_url, **kwargs)

    def get_post_count(self, feed):
        return len(self.Entry.objects.get_sort_index(feed.feed_url))

    @property
    def Entry(self):
        if self._entry is None:
            self._entry = self.get_post_model()
        return self._entry
