from celery.utils import get_cls_by_name

from djangofeeds import conf

BACKEND_ALIASES = {
    "database": "djangofeeds.backends.database.DatabaseBackend",
    "redis": "djangofeeds.backends.pyredis.RedisBackend",
}

_backend_cache = {}


def get_backend_cls(backend):
    if backend not in _backend_cache:
        _backend_cache[backend] = get_cls_by_name(backend, BACKEND_ALIASES)
    return _backend_cache[backend]


def backend_or_default(backend=None):
    backend = backend or conf.POST_STORAGE_BACKEND
    if isinstance(backend, basestring):
        return get_backend_cls(backend)()
    return backend
