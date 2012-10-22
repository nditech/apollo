#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8


# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #


# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "rapidsms.sqlite3",
    }
}

TIME_ZONE = 'Africa/Lagos'

# the rapidsms backend configuration is designed to resemble django's
# database configuration, as a nested dict of (name, configuration).
#
# the ENGINE option specifies the module of the backend; the most common
# backend types (for a GSM modem or an SMPP server) are bundled with
# rapidsms, but you may choose to write your own.
#
# all other options are passed to the Backend when it is instantiated,
# to configure it. see the documentation in those modules for a list of
# the valid options for each.
INSTALLED_BACKENDS = {
    "httptester": {
        "ENGINE": "threadless_router.backends.httptester.backend",
    },
    "mockbackend": {
        "ENGINE": "rapidsms.tests.harness",
    },
}

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [

    # the essentials.
    "django_nose",
    "djtables",
    "rapidsms",
    "zimbabwe",
    "core",
    "django_dag",
    "messagelog",

    # threadless router replacements
    "threadless_router.backends.httptester",
    "threadless_router.backends.kannel",

    "rapidsms.contrib.default",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.comments",

    "djcelery",
    "reversion",
    'bootstrap-pagination',
]

MAKO_TEMPLATE_DIRS = (
    'webapp/templates',
    'zambia/templates',
)

# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #

# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = False

# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"

# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

# for some reason this setting is blank in django's global_settings.py,
# but it is needed for static assets to be linkable.
MEDIA_URL = "/media/"

STATIC_URL = "/assets/"

STATIC_ROOT = "assets/"

# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1

# the default log settings are very noisy.
LOG_LEVEL = "DEBUG"
LOG_FILE = "rapidsms.log"
LOG_FORMAT = "[%(name)s]: %(message)s"
LOG_SIZE = 8192  # 8192 bits = 8 kb
LOG_BACKUPS = 256  # number of logs to keep

# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    "djcelery",
]

# the project-level url patterns
ROOT_URLCONF = "urls"
#SESSION_COOKIE_AGE=900
PROJECT_NAME = 'Apollo'
AUTHENTICATE_OBSERVER = False  # determines whether to authenticate the observer's phone number
ALLOWED_PUNCTUATIONS = '!'  # allowed punctuations in SMS forms
CHARACTER_TRANSLATIONS = (
    ('i', '1'),
    ('o', '0'),
    ('l', '1'),
    )
BACKLOG_DAYS = 4  # Number of days allowed for a submission to be updated by an observer

PAGE_SIZE = 30  # Number of submissions viewable per page

DEFAULT_CONNECTION_INDEX = 0

SMS_PREFIX = ''
SMS_SENDER = ''
SMS_USER = ''
SMS_PASS = ''
PHONE_CC = []

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'audit_log.middleware.UserLoggingMiddleware',
    'core.middleware.AllowOriginMiddleware',
    'djangomako.middleware.MakoMiddleware')

# celery queue settings
BROKER_URL = 'librabbitmq://guest:guest@localhost:5672/apollo'

# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
import os
import tempfile
import sys

if 'test' in sys.argv:
    for db_name in DATABASES:
        DATABASES[db_name]['TEST_NAME'] = os.path.join(
            tempfile.gettempdir(),
            "%s.rapidsms.test.sqlite3" % db_name)

try:
    from local_settings import *
except ImportError:
    pass

import djcelery
djcelery.setup_loader()
