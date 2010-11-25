import time
import urllib
import re
from sgmllib import SGMLParser
import html5lib

from base64 import b64encode
from datetime import datetime, timedelta

from django.utils.text import truncate_html_words
from django.utils.hashcompat import md5_constructor

from djangofeeds import conf
from djangofeeds.optimization import BeaconRemover
beacon_remover = BeaconRemover()

GUID_FIELDS = frozenset(("title", "link", "author"))


def format_date(t):
    """Make sure time object is a :class:`datetime.datetime` object."""
    if isinstance(t, time.struct_time):
        return datetime(*t[:6])
    return t


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


def search_links_url(url, source=''):
    """
    Search for rss links in html file.
    This method can be used if the search_alternate_links function
    failed to find any link.
    """
    rss_xml = 'application/rss+xml'
    atom_xml = 'application/atom+xml'

    def _map(link):
        """ add the url if to the link if doesn't start with http
            ie: "/rss.xml"
        """
        if link.startswith('http'):
            return link
        elif link.startswith('/'):
            # use the url as the domain, need to remove the / of the link
            return url + link[1:]
        else:
            return url + link

    class URLLister(SGMLParser):
        def reset(self):
            SGMLParser.reset(self)
            self.feeds = []

        def start_link(self, attrs):
            d = dict(attrs)
            try:
                if d['type'] == rss_xml or d['type'] == atom_xml:
                    self.feeds.append(d['href'])
            except KeyError:
                pass

    def lxml_parse(html):
        doc = html5lib.parse(html, treebuilder="lxml")
        links = []
        for type_link in [atom_xml, rss_xml]:
            nodes = doc.xpath("//head/link[@type='%s']" % type_link)
            links.extend([link.attrib['href'] for link in nodes])
        return links

    def regex_html(html):
        regex = re.compile(r"""
                <\s*link[^>]*   # contains link
                type\s*=\s*["|']application/(%s)\+xml['|"][^>]*  # the type
                href\s*=\s*["|'](?P<href>[^"']*)["|'][^>]*>    # save the href
                """ % "|".join(["atom", "rss"]), re.VERBOSE)
        elements = regex.findall(html)
        # elements list of (type, href). Return the href only
        return [elem[1] for elem in elements]

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

    # SGML Parser
    #parser = URLLister()
    #parser.feed(source)
    #parser.close()
    # lxml parser
    #links = lxml_parse(source)
    # regex
    links = regex_html(source)
    # Check that the urls are well formed
    return map(_map, links)


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
    now = datetime.now()

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

    try:
        content = truncate_html_words(content, conf.DEFAULT_ENTRY_WORD_LIMIT)
    except UnicodeDecodeError:
        content = ""

    return beacon_remover.strip(content)


def date_to_datetime(field_name):
    """Given a post field, convert its :mod:`feedparser` date tuple to
    :class:`datetime.datetime` objects.

    :param field_name: The post field to use.

    """

    def _field_to_datetime(feed_obj, entry):
        if field_name in entry:
            try:
                time_ = time.mktime(entry[field_name])
                date = datetime.fromtimestamp(time_)
            except TypeError:
                date = datetime.now()
            return date
        return datetime.now()
    _field_to_datetime.__doc__ = "Convert %s to datetime" % repr(field_name)

    return _field_to_datetime
