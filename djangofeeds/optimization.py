from httplib2 import Http
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError
from django.conf import settings
import re

DJANGOFEEDS_REMOVE_BEACON = getattr(settings,
    "DJANGO_FEEDS_REMOVE_BEACON", True)

# for now only the obvious tracker images
DJANGOFEEDS_BEACON_SERVICES = [
    r'http://feeds.feedburner.com/~r/.+',
    r'http://ads.pheedo.com/.+',
    r'http://a.rfihub.com/.+',
]

"""
Beacon detector use case
=========================

The idea is to remove some tracker images in the feeds because these images
are a pollution to the user.

Identified tools that add tracker images and tools into the feeds

    * Feedburner toolbar -- 4 toolbar images, 1 tracker image.
    * Pheedcontent.com toolbar -- 4 toolbar images, 1 advertisement image.
    * Digg/Reddit generic toolbar - 3 toolbar, no tracker image.
    * http://res.feedsportal.com/ -- 2 toolbar images, 1 tracker image.
    * http://a.rfihub.com/ -- associated with http://rocketfuelinc.com/,
        used for ads or tracking. Not quite sure.

About 80% of them use feedburner. Few use case of feeds:

feedburner toolbar and tracker
-------------------------------

    * WULFMORGENSTALLER
    * MarketWatch.com - Top Stories
    * Hollywood.com - Recent News
    * Wired: entertainement
    * Livescience.com
    * Reader Digest

Pheedcontent.com toolbar
--------------------------

    * Sports News : CBSSports.com

Digg/Reddit toolbar
-------------------

    * Abstruse goose

http://res.feedsportal.com/
------------------

    * New scientist.com

"""

class BeaconRemover(object):

    def looks_like_beacon(self, image_url):
        """Return True if the image URL has to be removed."""
        for reg in DJANGOFEEDS_BEACON_SERVICES:
            if re.match(reg, image_url):
                return True
        return False

    def strip(self, text):
        """This method is called by the parser."""
        if not DJANGOFEEDS_REMOVE_BEACON:
            return text
        # to avoid unecessary parsing
        if "<img" not in text:
            return text
        try:
            return self.parse_and_strip(text)
        except HTMLParseError:
            return text

    def parse_and_strip(self, html):
        """Do the stripping work using beautiful soup."""
        soup = BeautifulSoup(html)
        stripped_count = 0
        for image in soup("img"):
            image_source = image.get("src")
            if image_source and "://" in image_source:
                if self.looks_like_beacon(image_source):
                    image.replaceWith("")
                    stripped_count += 1
        return str(soup) if stripped_count else html
