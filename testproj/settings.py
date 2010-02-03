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

AMQP_SERVER = "localhost"
AMQP_PORT = 5672
AMQP_VHOST = "/"
AMQP_USER = "guest"
AMQP_PASSWORD = "guest"

CELERY_AMQP_EXCHANGE = "testdjangofeeds"
CELERY_AMQP_ROUTING_KEY = "testdjangofeeds"
CELERY_AMQP_CONSUMER_QUEUE = "testdjangofeeds"

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
