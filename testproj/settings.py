# Django settings for testproj project.

import os
import sys
# import source code dir
sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

SITE_ID = 69932

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ROOT_URLCONF = "urls"

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

TEST_RUNNER = "djangofeeds.tests.runners.run_tests"
TEST_APPS = (
    "djangofeeds",
)

COVERAGE_EXCLUDE_MODULES = ("djangofeeds.__init__",
                            "djangofeeds.admin",
                            "djangofeeds.maintenance",
                            "djangofeeds.management.*",
                            "djangofeeds.optimization",
                            "djangofeeds.tests.*",
)
COVERAGE_HTML_REPORT = True
COVERAGE_BRANCH_COVERAGE = True

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "/"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"

CELERY_DEFAULT_EXCHANGE = "testdjangofeeds"
CELERY_DEFAULT_QUEUE = "testdjangofeeds"
CELERY_QUEUES = {
    "testdjangofeeds": {
        "binding_key": "testdjangofeeds",
    }
}
CELERY_DEFAULT_ROUTING_KEY = "testdjangofeeds"


MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'testdb.sqlite'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djangofeeds',
)

try:
    import test_extensions
except ImportError:
    pass
else:
    INSTALLED_APPS += ("test_extensions", )

SEND_CELERY_TASK_ERROR_EMAILS = False
