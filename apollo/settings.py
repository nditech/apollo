# -*- coding: utf-8 -*-
from datetime import timedelta
from urllib.parse import urlparse
import numpy
import os
import string

from prettyconf import config


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

config.starting_path = PROJECT_ROOT


try:
    SECRET_KEY = config('SECRET_KEY')
except KeyError:
    raise KeyError('A SECRET_KEY value must be defined in the environment.')

DEBUG = config('DEBUG', cast=config.boolean, default=False)
PAGE_SIZE = config('PAGE_SIZE', cast=int, default=25)

MONGODB_SETTINGS = {
    'DB': config('MONGO_DATABASE_NAME', default='apollo').strip(),
    'HOST': urlparse(
        config('MONGODB_PORT', default='mongodb://localhost')).netloc
}

# default to UTC for prior deployments
TIMEZONE = config('TIMEZONE', default='UTC')

SSL_REQUIRED = config('SSL_REQUIRED', cast=config.boolean, default=True)
ENABLE_MOE = config('ENABLE_MOE', cast=config.boolean, default=False)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

# This setting informs the application server of the number of
# upstream proxies to account for. Useful to determining true IP address
# for the request and preventing spoofing. Because this application is
# designed to be run behind a proper webserver, the default is set to 1
UPSTREAM_PROXY_COUNT = config('UPSTREAM_PROXY_COUNT', cast=int, default=1)

SENTRY_DSN = config('SENTRY_DSN', default=None)
SENTRY_USER_ATTRS = ['email']

SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = '/accounts'
SECURITY_POST_LOGOUT_VIEW = '/accounts/login'
SECURITY_LOGIN_USER_TEMPLATE = 'frontend/login_user.html'
SECURITY_EMAIL_SENDER = config('SECURITY_EMAIL_SENDER', default=None)
SECURITY_SEND_REGISTER_EMAIL = config(
    'SECURITY_SEND_REGISTER_EMAIL', cast=config.boolean, default=False)
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SESSION_COOKIE_SECURE = True if SSL_REQUIRED else False
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

MAIL_SERVER = config('MAIL_SERVER', default=None)
MAIL_PORT = config('MAIL_PORT', default=None)
MAIL_USE_TLS = config('MAIL_USE_TLS', cast=config.boolean, default=False)
MAIL_USE_SSL = config('MAIL_USE_SSL', cast=config.boolean, default=False)
MAIL_USERNAME = config('MAIL_USERNAME', default=None)
MAIL_PASSWORD = config('MAIL_PASSWORD', default=None)
DEFAULT_EMAIL_SENDER = SECURITY_EMAIL_SENDER

CELERY_BROKER_URL = 'redis://{host}/{database}'.format(
    host=urlparse(
        config('REDIS_PORT', default='redis://localhost')).netloc,
    database=config('REDIS_DATABASE', default='0'))
CELERY_RESULT_BACKEND = 'redis://{host}/{database}'.format(
    host=urlparse(
        config('REDIS_PORT', default='redis://localhost')).netloc,
    database=config('REDIS_DATABASE', default='0'))
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CACHE_TYPE = 'simple' if DEBUG else 'redis'
CACHE_REDIS_URL = 'redis://{host}/{database}'.format(
    host=urlparse(
        config('REDIS_PORT', default='redis://localhost')).netloc,
    database=config('REDIS_DATABASE', default='0'))

LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'az': 'Azərbaycanca',
    'ar': 'العربية',
    'de': 'Deutsch',
    'ru': 'Русский',
    'ro': 'Română',
}
BABEL_DEFAULT_LOCALE = config('BABEL_DEFAULT_LOCALE', default='en')

ALLOWED_PUNCTUATIONS = '!'
CHARACTER_TRANSLATIONS = (
    ('i', '1'),
    ('I', '1'),
    ('o', '0'),
    ('O', '0'),
    ('l', '1'),
    ('L', '1'),
)
PUNCTUATIONS = [s for s in string.punctuation if s not in ALLOWED_PUNCTUATIONS] + [' ']
TRANS_TABLE = dict((ord(char_from), ord(char_to))
                   for char_from, char_to in
                   CHARACTER_TRANSLATIONS)
MESSAGING_OUTGOING_GATEWAY = config(
    'MESSAGING_OUTGOING_GATEWAY',
    cast=config.eval,
    default='''{
        'type': 'kannel',
        'gateway_url': 'http://localhost:13013/cgi-bin/sendsms',
        'username': 'foo',
        'password': 'bar'
    }''')
MESSAGING_CC = config('MESSAGING_CC', cast=config.tuple, default=tuple())
MESSAGING_SECRET = config('MESSAGING_SECRET', default=None)

APPLICATIONS = config(
    'APPLICATIONS',
    cast=config.eval,
    default='''("apollo.frontend",
        "apollo.locations",
        "apollo.participants",
        "apollo.formsframework",
        "apollo.submissions",
        "apollo.messaging",
        "apollo.process_analysis",
        "apollo.result_analysis",
        "apollo.odk")''')

BIG_N = config('BIG_N', cast=int, default=0) or numpy.inf
GOOGLE_ANALYTICS_KEY = config('GOOGLE_ANALYTICS_KEY', default=None)

TRANSLATE_CHARS = config('TRANSLATE_CHARS', cast=config.boolean, default=True)
TRANSLITERATE_INPUT = config('TRANSLITERATE_INPUT', cast=config.boolean, default=False)
TRANSLITERATE_OUTPUT = config('TRANSLITERATE_OUTPUT', cast=config.boolean, default=False)


# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='sqlite:///:memory:')
SQLALCHEMY_ECHO = DEBUG
SQLALCHEMY_TRACK_MODIFICATIONS = False
