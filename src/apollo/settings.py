#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4

import ast
import os
import dj_database_url
import dotenv

dotenv.read_dotenv(os.path.normpath(os.path.dirname(__file__) + os.sep + '..' + os.sep + '..' + os.sep + '.env'))
ugettext = lambda s: s

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #


# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": dj_database_url.config(default='sqlite://rapidsms.sqlite3')
}

TIME_ZONE = os.environ.get('APOLLO_TIMEZONE', 'Africa/Lagos')

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
        "ENGINE": "rapidsms.contrib.httptester.backend.HttpTesterCacheBackend",
    },
    "kannel": {
        "ENGINE": "rapidsms.backends.kannel.outgoing.KannelBackend",
    }
}

BULKSMS_BACKEND = os.environ.get('APOLLO_BULKSMS_BACKEND', 'kannel')

BULKSMS_ROUTES = {
    'default': 'kannel'
}

RAPIDSMS_ROUTER = "rapidsms.router.db.DatabaseRouter"

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [

    # the essentials.
    "core",
    "messagelog",

    "django_nose",
    "rapidsms",
    "django_dag",
    "south",
    "tastypie",
    "guardian",
    "jimmypage",
    "vinaigrette",

    "rapidsms.contrib.default",
    "rapidsms.router.db",

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
    "django.contrib.humanize",
    "django.contrib.gis",

    "djcelery",
    "reversion",
    "bootstrap-pagination",
    "pipeline",
]

# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #

# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = ast.literal_eval(os.environ.get('APOLLO_DEBUG', 'False'))

INTERNAL_IPS = ('127.0.0.1',)

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
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

USE_L10N = True
ANONYMOUS_USER_ID = -1
GUARDIAN_RENDER_403 = True

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
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 1800
PROJECT_NAME = 'Apollo'
AUTHENTICATE_OBSERVER = False  # determines whether to authenticate the observer's phone number
ALLOWED_PUNCTUATIONS = '!'  # allowed punctuations in SMS forms
CHARACTER_TRANSLATIONS = (
    ('i', '1'),
    ('o', '0'),
    ('l', '1'),
)
LOCATIONS_GRAPH_MAXAGE = 25200  # number of seconds to cache the locations graph - 1wk
PAGE_SIZE = 10  # Number of submissions viewable per page

FLAG_STATUSES = {
    'no_problem': ('0', 'No Problem'),
    'problem': ('2', 'Problem'),
    'serious_problem': ('3', 'Serious Problem'),
    'verified': ('4', 'Verified'),
    'rejected': ('5', 'Rejected')
}

FLAG_CHOICES = (
    ('0', 'No Problem'),
    ('2', 'Problem'),
    ('3', 'Serious Problem'),
    ('4', 'Verified'),
    ('5', 'Rejected')
)

STATUS_CHOICES = (
    ('', 'Status'),
    ('0', 'Status — No Problem'),
    ('2', 'Status — Unverified'),
    ('4', 'Status — Verified'),
    ('5', 'Status — Rejected')
)

BIG_N = 6000000  # Big N

DEFAULT_CONNECTION_INDEX = 0
ENABLE_MULTIPLE_PHONES = False  # determines whether to allow for multiple numbers to be set for observers

PHONE_CC = []

MIDDLEWARE_CLASSES = (
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'johnny.middleware.LocalStoreClearMiddleware',
    'johnny.middleware.QueryCacheMiddleware',
    'core.middleware.AllowOriginMiddleware',
    'core.middleware.KMLMiddleware',)

# celery queue settings
BROKER_URL = os.environ.get('APOLLO_BROKER_URL', 'librabbitmq://guest:guest@localhost:5672/apollo')

# caching
CACHES = {
    'graph': {
        'BACKEND': 'apollo.core.memcached.BigMemcachedCache',
        'OPTIONS': {
            'MAX_VALUE_LENGTH': 2 * 1024 * 1024
        },
        'LOCATION': '127.0.0.1:11211',
    },
    'default': {
        'BACKEND': 'johnny.backends.memcached.MemcachedCache',
        'LOCATION': ['127.0.0.1:11211'],
        'JOHNNY_CACHE': True,
    }
}

JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_apollo'
JIMMY_PAGE_CACHE_PREFIX = "jp_apollo"
JIMMY_PAGE_DISABLED = True

# django-pipeline settings
PIPELINE_CSS = {
    'apollo': {
        'source_filenames': (
          'css/bootstrap.css',
          'css/bootstrap-responsive.css',
          'css/select2.css',
          'css/table-fixed-header.css',
          'css/datepicker.css',
          'css/jquery.qtip.css',
          'css/custom.css',
        ),
        'output_filename': 'css/apollo.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

PIPELINE_JS = {
    'apollo': {
        'source_filenames': (
            'js/jquery.js',
            'js/bootstrap.js',
            'js/select2.js',
            'js/bootstrap-datepicker.js',
            'js/table-fixed-header.js',
            'js/protovis.js',
            'js/custom.js',
        ),
        'output_filename': 'js/apollo.js',
    }
}

SMS_LANGUAGE_CODE = os.environ.get('APOLLO_SMS_LANGUAGE_CODE', 'en')
LANGUAGE_CODE = 'en-us'

LANGUAGES = (
  ('en', ugettext('English')),
  ('az', ugettext('Azerbaijani')),
  ('fr', ugettext('French')),
)

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
