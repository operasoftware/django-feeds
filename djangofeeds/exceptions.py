from httplib import NOT_FOUND as HTTP_NOT_FOUND


class TimeoutError(Exception):
    """The operation timed-out."""


class FeedCriticalError(Exception):
    """An unrecoverable error happened that the user must deal with."""
    status = None

    def __init__(self, msg, status=None):
        if status:
            self.status = status
        super(FeedCriticalError, self).__init__(msg, self.status)


class FeedNotFoundError(FeedCriticalError):
    """The feed URL provieded does not exist."""
    status = HTTP_NOT_FOUND
