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

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

COVERAGE_EXCLUDE_MODULES = ("djangofeeds",
                            "djangofeeds.admin",
                            "djangofeeds.maintenance",
                            "djangofeeds.management*",
                            "djangofeeds.tests*",
                            "djangofeeds.models",
                            "djangofeeds.managers",
                            "djangofeeds.utils",
)

TEST_RUNNER = "django_nose.run_tests"
here = os.path.abspath(os.path.dirname(__file__))
NOSE_ARGS = [os.path.join(here, os.pardir, "djangofeeds", "tests"),
            "--cover3-package=djangofeeds",
            "--cover3-branch",
            "--cover3-exclude=%s" % ",".join(COVERAGE_EXCLUDE_MODULES)]


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
    'django_nose',
    'djcelery',
    'djangofeeds',
)


SEND_CELERY_TASK_ERROR_EMAILS = False

if os.environ.get("TEST_REDIS_POSTS"):
    DJANGOFEEDS_POST_STORAGE_BACKEND = "redis"
