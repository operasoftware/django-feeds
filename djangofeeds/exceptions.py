import httplib as http


class TimeoutError(Exception):
    """The operation timed-out."""


class FeedCriticalError(Exception):
    """An unrecoverable feed error happened.

    :keyword status: Optional HTTP status code associated with the error.

    """
    def __init__(self, msg, status=None):
        self.status = status
        super(FeedCriticalError, self).__init__(msg, status)


class FeedNotFoundError(FeedCriticalError):
    """The feed URL provided did not exist."""
    status = http.NOT_FOUND
