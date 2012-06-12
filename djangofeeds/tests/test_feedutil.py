try:
    import unittest2 as unittest
except ImportError:
    import unittest
import feedparser
from datetime import datetime
import pytz

from djangofeeds import feedutil
from djangofeeds.feedutil import date_to_datetime, find_post_content
from djangofeeds.tests.test_importers import get_data_file
from django.utils.timezone import utc

NOT_ENCODEABLE = ('\xd0\x9e\xd1\x82\xd0\xb2\xd0\xb5\xd1\x82\xd1\x8b '
                  '\xd0\xbd\xd0\xb0 \xd0\xb2\xd0\xb0\xd1\x88\xd0\xb8 '
                  '\xd0\xb2\xd0\xbe\xd0\xbf\xd1\x80\xd0\xbe\xd1\x81\xd1'
                  '\x8b \xd0\xbf\xd1\x80\xd0\xbe Mac')


class test_date_to_datetime(unittest.TestCase):

    def test_no_date(self):
        x = date_to_datetime("date_test")
        date = x(None, {})
        now = datetime.now(pytz.utc)
        self.assertTupleEqual((date.year, date.month, date.day),
                              (now.year, now.month, now.day))

    def test_wrong_type(self):
        x = date_to_datetime("date_test")
        date = x(None, {"date_test": object()})
        now = datetime.now(pytz.utc)
        self.assertTupleEqual((date.year, date.month, date.day),
                              (now.year, now.month, now.day))


class test_find_post_content(unittest.TestCase):

    def test_returns_empty_string_on_UnicodeDecodeError(self):

        def raise_UnicodeDecodeError(*args, **kwargs):
            return "quickbrown".encode("zlib").encode("utf-8")

        prev = feedutil.truncate_html_words
        feedutil.truncate_html_words = raise_UnicodeDecodeError
        try:
            self.assertEqual(find_post_content(None, {
                                "description": "foobarbaz"}), "")
        finally:
            feedutil.truncate_html_words = prev

    def test_get_img(self):
        """
        Check that find_post_content adds an image to the content if
        theres no img tag and is a media namespace
        """
        feed_str = get_data_file("dailymotion.rss")
        feed = feedparser.parse(feed_str)
        elements = ("http://ak2.static.dailymotion.com/static/video/454/"
                "695/26596454:jpeg_preview_large.jpg?20101129171226",
                "320",
                "240")

        post = find_post_content(None, feed.entries[0])
        for elem in elements:
            self.assertTrue(post.find(elem) != -1, elem)


class test_generate_guid(unittest.TestCase):

    def test_handles_not_encodable_text(self):
        entry = dict(title=NOT_ENCODEABLE, link="http://foo.com")
        guid = feedutil.generate_guid(entry)
        self.assertTrue(guid)

    def test_is_unique(self):
        entry1 = dict(title="First", link="http://foo1.com")
        feedutil.generate_guid(entry1)
        entry2 = dict(title="Second", link="http://foo1.com")
        feedutil.generate_guid(entry2)
        self.assertNotEqual(entry1, entry2)

    def test_utf8_url(self):
        """Try to reproduce a utf8 encoding error."""
        utf8_entry = dict(title="UTF-8",
            link="premi\xc3\xa8re_")
        feedutil.get_entry_guid(None, utf8_entry)

    def test_search_alternate_links(self):
        feed_str = get_data_file("bbc_homepage.html")
        feed = feedparser.parse(feed_str)
        links = feedutil.search_alternate_links(feed)
        self.assertListEqual(links, [
            "http://newsrss.bbc.co.uk/rss/newsonline_world_edition/"
            "front_page/rss.xml"])

        feed_str = get_data_file("newsweek_homepage.html")
        feed = feedparser.parse(feed_str)
        links = feedutil.search_alternate_links(feed)
        self.assertListEqual(links, [
            "http://feeds.newsweek.com/newsweek/TopNews"])


class test_alternate_links(unittest.TestCase):

    def test_search_alternate_links_double_function(self):
        feed_str = get_data_file("smp.no.html")
        feed = feedparser.parse(feed_str)
        links = feedutil.search_alternate_links(feed)
        self.assertListEqual(links,
            [u'http://www.smp.no/?service=rss',
            u'http://www.smp.no/?service=rss&t=0',
            u'http://www.smp.no/nyheter/?service=rss',
            u'http://www.smp.no/kultur/?service=rss']
        )
        links = feedutil.search_links_url("http://www.smp.no/", feed_str)
        self.assertListEqual(links,
            [u'http://www.smp.no/?service=rss',
            u'http://www.smp.no/?service=rss&amp;t=0',
            u'http://www.smp.no/nyheter/?service=rss',
            u'http://www.smp.no/kultur/?service=rss']
        )

    def test_search_links_order(self):
        """ Different order for type and href in link sentence.
            Format in UTF-8 (Russian)"""
        feed_str = get_data_file("mk.ru.html")
        links = feedutil.search_links_url("http://www.mk.ru/", feed_str)
        self.assertListEqual(links,
                ['http://www.mk.ru/rss/news/index.xml',
                 'http://www.mk.ru/rss/mk/index.xml']
        )

    def test_search_link_malformed(self):
        """ SGML and others are not able to parse it """
        feed_str = get_data_file("foxnews.com.html")
        links = feedutil.search_links_url("http://www.foxnews.com/", feed_str)
        self.assertListEqual(links,
                ['http://feeds.feedburner.com/foxnews/latest']
        )

    def test_search_links_mixed(self):
        """ Mixed atom and rss sentences """
        feed_str = get_data_file("elcomercio.pe.html")
        links = feedutil.search_links_url(
                "http://www.elcomercio.pe/", feed_str)
        self.assertListEqual(links,
            ['http://www.elcomercio.pe/feed/portada.xml',
             'http://www.elcomercio.pe/feed/portada/politica.xml',
             'http://www.elcomercio.pe/feed/portada/lima.xml',
             'http://www.elcomercio.pe/feed/portada/peru.xml',
             'http://www.elcomercio.pe/feed/portada/mundo.xml',
             'http://www.elcomercio.pe/feed/portada/economia.xml',
             'http://www.elcomercio.pe/feed/portada/tecnologia.xml',
             'http://www.elcomercio.pe/feed/portada/deportes.xml',
             'http://www.elcomercio.pe/feed/portada/espectaculos.xml',
             'http://www.elcomercio.pe/feed/portada/ecologia.xml',
             'http://www.elcomercio.pe/feed/portada/opinion.xml']
        )

    def test_serach_links_join_url(self):
        feed_str = get_data_file("chooseopera.html")
        links = feedutil.search_links_url(
                "http://my.opera.com/chooseopera/blog/", feed_str)

        self.assertListEqual(links,
                ['http://my.opera.com/chooseopera/xml/rss/blog/',
                 'http://my.opera.com/chooseopera/xml/atom/blog/'])
