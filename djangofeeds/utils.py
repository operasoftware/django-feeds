import logging
import pytz
from datetime import datetime
from django.utils.timezone import utc

from django.utils.translation import ungettext, ugettext as _

_logger = None

JUST_NOW = _("just now")
SECONDS_AGO = (_("%(seconds)d second ago"), _("%(seconds)d seconds ago"))
MINUTES_AGO = (_("%(minutes)d minute ago"), _("%(minutes)d minutes ago"))
HOURS_AGO = (_("%(hours)d hour ago"), _("%(hours)d hours ago"))
YESTERDAY_AT = _("yesterday at %(time)s")
OLDER_YEAR = (_("year"), _("years"))
OLDER_MONTH = (_("month"), _("months"))
OLDER_WEEK = (_("week"), _("weeks"))
OLDER_DAY = (_("day"), _("days"))
OLDER_CHUNKS = (
    (365.0, OLDER_YEAR),
    (30.0, OLDER_MONTH),
    (7.0, OLDER_WEEK),
    (1.0, OLDER_DAY),
)
OLDER_AGO = _("%(number)d %(type)s ago")


def _un(singular__plural, n=None):
    singular, plural = singular__plural
    return ungettext(singular, plural, n)


def naturaldate(date):
    """Convert datetime into a human natural date string."""

    if not date:
        return ''

    now = datetime.now(pytz.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=utc)
    delta = now - date
    delta_midnight = today - date

    days = delta.days
    hours = round(delta.seconds / 3600, 0)
    minutes = delta.seconds / 60

    if days < 0:
        return JUST_NOW

    if days == 0:
        if hours == 0:
            if minutes > 0:
                return _un(MINUTES_AGO, n=minutes) % {"minutes": minutes}
            else:
                return JUST_NOW
        else:
            return _un(HOURS_AGO, n=hours) % {"hours": hours}

    if delta_midnight.days == 0:
        return YESTERDAY_AT % {"time": date.strftime("%H:%M")}

    count = 0
    for chunk, singular_plural in OLDER_CHUNKS:
        if days >= chunk:
            count = round((delta_midnight.days + 1) / chunk, 0)
            type_ = _un(singular_plural, n=count)
            break

    return OLDER_AGO % {"number": count, "type": type_}


def truncate_by_field(field, value):
    """Truncate string value by the model fields ``max_length`` attribute.

    :param field: A Django model field instance.
    :param value: The value to truncate.

    """
    if isinstance(value, basestring) and \
            hasattr(field, "max_length") and value > field.max_length:
                return value[:field.max_length]
    return value


def truncate_field_data(model, data):
    """Truncate all data fields for model by its ``max_length`` field
    attributes.

    :param model: Kind of data (A Django Model instance).
    :param data: The data to truncate.

    """
    fields = dict((field.name, field) for field in model._meta.fields)
    return dict((name, truncate_by_field(fields[name], value))
                    for name, value in data.items())


def get_default_logger():
    """Get the default logger for this application."""
    global _logger

    if _logger is None:
        _logger = logging.getLogger("djangofeeds")
        channel = logging.StreamHandler()
        _logger.addHandler(channel)
        _logger.setLevel(logging.WARNING)
    return _logger
