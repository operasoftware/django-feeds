"""Django Feed Aggregator."""
VERSION = (0, 2, 16)
__version__ = ".".join(map(str, VERSION))
__author__ = "Ask Solem"
__contact__ = "askh@opera.com"
__homepage__ = "http://github.com/ask/django-feeds/"
__docformat__ = "restructuredtext"

import logging

logger = logging.getLogger("djangofeeds")
channel = logging.StreamHandler()
logger.addHandler(channel)
logger.setLevel(logging.WARNING)
