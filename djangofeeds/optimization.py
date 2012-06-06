import BeautifulSoup
from HTMLParser import HTMLParseError
from django.conf import settings
import re

DJANGOFEEDS_REMOVE_TRACKERS = getattr(settings,
    "DJANGOFEEDS_REMOVE_TRACKERS", True)

# The obvious tracker images
DJANGOFEEDS_TRACKER_SERVICES = getattr(settings,
    "DJANGOFEEDS_TRACKER_SERVICES", [
    'http://feedads',
    'http://feeds.feedburner.com/~r/',
    'http://feeds.feedburner.com/~ff/',
    'http://rss.feedsportal.com/c/',
    'http://ads.pheedo.com/',
    'http://a.rfihub.com/',
    'http://segment-pixel.invitemedia.com/',
    'http://pixel.quantserve.com/',
    'http://feeds.newscientist.com/',
    'http://mf.feeds.reuters.com/c/',
    'http://telegraph.feedsportal.com/c/',
])

DJANGOFEEDS_SMALL_IMAGE_LIMIT = getattr(settings,
    "DJANGOFEEDS_SMALL_IMAGE_LIMIT", 50)


class PostContentOptimizer(object):
    """Remove diverse abberation and annoying content in the posts.

    The idea is to remove some tracker images in the feeds because
    these images are a pollution to the user.

    Identified tools that add tracker images and tools into the feeds

    * Feedburner toolbar -- 4 toolbar images, 1 tracker image.
    * Pheedcontent.com toolbar -- 4 toolbar images, 1 advertisement image.
    * Digg/Reddit generic toolbar - 3 toolbar, no tracker image.
    * http://res.feedsportal.com/ -- 2 toolbar images, 1 tracker image.
    * http://a.rfihub.com/ -- associated with http://rocketfuelinc.com/,
        used for ads or tracking. Not quite sure.

    About 80% of them use feedburner. Few use cases of feeds:

    * feedburner toolbar and tracker

        * WULFMORGENSTALLER
        * MarketWatch.com - Top Stories
        * Hollywood.com - Recent News
        * Wired: entertainement
        * Livescience.com
        * Reader Digest

    * Pheedcontent.com toolbar

        * Sports News : CBSSports.com

    * Digg/Reddit toolbar

        * Abstruse goose

    * http://res.feedsportal.com/

        * New scientist.com

    """

    def looks_like_tracker(self, url):
        """Return True if the image URL has to be removed."""
        for service in DJANGOFEEDS_TRACKER_SERVICES:
            if url.startswith(service):
                return True
        return False

    def optimize(self, html):
        """Remove unecessary spaces, <br> and image tracker."""

        # Remove uneccesary white spaces
        html = html.strip()
        try:
            soup = BeautifulSoup.BeautifulSoup(html)
            self.remove_excessive_br(soup)
            if DJANGOFEEDS_REMOVE_TRACKERS:
                self.remove_trackers(soup)
        except HTMLParseError:
            return html

        return str(soup).strip()

    def remove_excessive_br(self, soup):
        # start with true to remove any starting br tag
        last_one_is_br = True
        children = soup.childGenerator()
        for el in children:
            if isinstance(el, BeautifulSoup.Tag):
                if el.name == 'br':
                    if last_one_is_br:
                        el.replaceWith("")
                    last_one_is_br = True
                else:
                    last_one_is_br = False

    def remove_trackers(self, soup):
        """Remove the trackers."""
        stripped_count = 0
        for image in soup("img"):
            already_removed = False

            # remove images that looks like tracker
            image_source = image.get("src", "")
            if (len(image_source) == 0 or
                self.looks_like_tracker(image_source)):
                image.replaceWith("")
                already_removed = True

            # remove small images
            try:
                image_width = int(image.get("width",
                    DJANGOFEEDS_SMALL_IMAGE_LIMIT))
            except ValueError:
                image_width = None
            if (image_width is not None and
                image_width < DJANGOFEEDS_SMALL_IMAGE_LIMIT and
                not already_removed):
                image.replaceWith("")

        # remove links that looks like tracker
        for link in soup("a"):
            link_href = link.get("href")
            if link_href and "://" in link_href:
                if self.looks_like_tracker(link_href):
                    link.replaceWith("")
