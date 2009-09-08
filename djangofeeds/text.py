from django.utils.text import truncate_words, truncate_html_words
from djangofeeds import conf


def summarize(text, max_length=conf.DEFAULT_SUMMARY_MAX_WORDS):
    """Truncate words by ``max_length``."""
    return truncate_words(text.encode("utf-8"), max_length)


def summarize_html(text, max_length=conf.DEFAULT_SUMMARY_MAX_WORDS):
    """Truncate HTML by ``max_length``."""
    return truncate_html_words(text.encode("utf-8"), max_length)
