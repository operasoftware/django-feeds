import time
import urllib
import urllib2
import re
import pytz

from base64 import b64encode
from datetime import datetime, timedelta

from django.utils.text import truncate_html_words
from django.utils.hashcompat import md5_constructor

from djangofeeds import conf
from djangofeeds.optimization import PostContentOptimizer
from django.utils.timezone import utc
feed_content_optimizer = PostContentOptimizer()

GUID_FIELDS = frozenset(("title", "link", "author"))


def format_date(t):
    """Make sure time object is a :class:`datetime.datetime` object."""
    if isinstance(t, time.struct_time):
        return datetime(*t[:6], tzinfo=pytz.utc)
    return t.replace(tzinfo=utc)


def md5sum(text):
    """Return the md5sum of a text string."""
    return md5_constructor(text).hexdigest()


def safe_encode(value):
    """Try encode unicode value, if that's not possible encode it with
    b64 encoding."""
    try:
        return value.encode("utf-8")
    except UnicodeDecodeError:
        return b64encode(value)


def generate_guid(entry):
    """Generate missing guid for post entry."""
    return md5sum("|".join(safe_encode(entry.get(key) or "")
                              for key in GUID_FIELDS))


def search_alternate_links(feed):
    """Search for alternate links into a parsed feed."""
    if not feed.get("entries", 1):
        return [link.get("href") or ""
                    for link in feed["feed"].get("links") or []
                        if "rss" in link.get("type")]
    return []


links = re.compile(r"""<\s*link[^>]*>""")
atom = re.compile(r"""<[^>]*
    type\s*=\s*["|']application/atom\+xml['|"][^>]*
    >""", re.VERBOSE)
rss = re.compile(r"""<[^>]*
    type\s*=\s*["|']application/rss\+xml['|"][^>]*
    >""", re.VERBOSE)
href = re.compile(r"""href\s*=\s*["|'](?P<href>[^"']*)["|'][^>]*""")


def regex_html(html):
    links_str = "".join(links.findall(html))
    types_str = "".join(rss.findall(links_str) + atom.findall(links_str))
    return href.findall(types_str)


def search_links_url(url, source=''):
    """
    Search for rss links in html file.
    This method can be used if the search_alternate_links function
    failed to find any link.
    """

    # For testing we pass directly the html in source
    if not source:
        try:
            sock = urllib.urlopen(url)
        except IOError, e:
            return []
        try:
            source = sock.read()
        finally:
            sock.close()

    links = regex_html(source)
    return [urllib2.urlparse.urljoin(url, link) for link in links]


def get_entry_guid(feed_obj, entry):
    """Get the guid for a post.

    If the post doesn't have a guid, a new guid is generated.

    """
    if "guid" not in entry:
        return generate_guid(entry)

    guid = entry["guid"]
    try:
        guid = guid.encode("utf-8").strip()
    except UnicodeDecodeError:
        guid = guid.strip()
    return guid


def entries_by_date(entries, limit=None):
    """Sort the feed entries by date

    :param entries: Entries given from :mod:`feedparser``.
    :param limit: Limit number of posts.

    """
    now = datetime.now(pytz.utc)

    def find_date(entry, counter):
        """Find the most current date entry tuple."""

        return (entry.get("updated_parsed") or
                entry.get("published_parsed") or
                entry.get("date_parsed") or
                now - timedelta(seconds=(counter * 30)))

    sorted_entries = []
    for counter, entry in enumerate(entries):
        date = format_date(find_date(entry, counter))
        # the found date is put into the entry
        # because some feed just don't have any valid dates.
        # This will ensure that the posts will be properly ordered
        # later on when put into the database.
        entry["updated_parsed"] = date.timetuple()
        entry["published_parsed"] = entry.get("published_parsed") or \
                                        date.timetuple()
        sorted_entries.append((date, entry))

    sorted_entries.sort(key=lambda key: key[0])
    sorted_entries.reverse()
    return [entry for _date, entry in sorted_entries[:limit]]


def find_post_content(feed_obj, entry):
    """Find the correct content field for a post."""
    try:
        content = entry["content"][0]["value"]
    except (IndexError, KeyError):
        content = entry.get("description") or entry.get("summary") or ""

    if '<img' not in content:
        # if there's no image and the we add an image to the feed
        def build_img(img_dict):
            try:
                # The tag is url instead of src... pain
                img = "<img src='%s'" % img_dict.get("url")
            except KeyError:
                return ''
            img_dict.pop('url')
            for attr in img_dict.items():
                img += "%s='%s'" % (attr[0], attr[1])
            img += ">"
            return img

        try:
            thumbnail = entry["media_thumbnail"][0]
            img = build_img(thumbnail)
        except (IndexError, KeyError):
            img = ""
        content = img + content
    try:
        content = truncate_html_words(content, conf.DEFAULT_ENTRY_WORD_LIMIT)
    except UnicodeDecodeError:
        content = ""

    return feed_content_optimizer.optimize(content)


def date_to_datetime(field_name):
    """Given a post field, convert its :mod:`feedparser` date tuple to
    :class:`datetime.datetime` objects.

    :param field_name: The post field to use.

    """

    def _field_to_datetime(feed_obj, entry):
        if field_name in entry:
            try:
                time_ = time.mktime(entry[field_name])
                date = datetime.fromtimestamp(time_).replace(tzinfo=utc)
            except TypeError:
                date = datetime.now(pytz.utc)
            return date
        return datetime.now(pytz.utc)
    _field_to_datetime.__doc__ = "Convert %s to datetime" % repr(field_name)

    return _field_to_datetime
