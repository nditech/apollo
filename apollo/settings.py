# -*- coding: utf-8 -*-
from datetime import timedelta
from urlparse import urlparse
import ast
import numpy
import os
import string

try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    raise KeyError('A SECRET_KEY value must be defined in the environment.')

DEBUG = ast.literal_eval(
    os.environ.get('DEBUG', 'False'))
PAGE_SIZE = ast.literal_eval(
    os.environ.get('PAGE_SIZE', '25'))

MONGODB_SETTINGS = {
    'DB': os.environ.get('MONGO_DATABASE_NAME', 'apollo').strip(),
    'HOST': urlparse(
        os.environ.get('MONGODB_PORT', 'mongodb://localhost')).netloc
}

# default to UTC for prior deployments
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

SSL_REQUIRED = ast.literal_eval(
    os.environ.get('SSL_REQUIRED', 'True'))
ENABLE_MOE = ast.literal_eval(
    os.environ.get('ENABLE_MOE', 'False'))
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')

# This setting informs the application server of the number of
# upstream proxies to account for. Useful to determining true IP address
# for the request and preventing spoofing. Because this application is
# designed to be run behind a proper webserver, the default is set to 1
UPSTREAM_PROXY_COUNT = os.environ.get('UPSTREAM_PROXY_COUNT', 1)

SENTRY_DSN = os.environ.get('SENTRY_DSN')

SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = '/accounts'
SECURITY_POST_LOGOUT_VIEW = '/accounts/login'
SECURITY_LOGIN_USER_TEMPLATE = 'frontend/login_user.html'
SECURITY_EMAIL_SENDER = os.environ.get('SECURITY_EMAIL_SENDER')
SECURITY_SEND_REGISTER_EMAIL = ast.literal_eval(
    os.environ.get('SECURITY_SEND_REGISTER_EMAIL', 'False'))
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SESSION_COOKIE_SECURE = True if SSL_REQUIRED else False
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost').strip()
MAIL_PORT = os.environ.get('MAIL_PORT', 25)
MAIL_USE_TLS = ast.literal_eval(os.environ.get('MAIL_USE_TLS', 'False'))
MAIL_USE_SSL = ast.literal_eval(os.environ.get('MAIL_USE_SSL', 'False'))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
DEFAULT_EMAIL_SENDER = SECURITY_EMAIL_SENDER

CELERY_BROKER_URL = 'redis://{host}/{database}'.format(
    host=urlparse(
        os.environ.get('REDIS_PORT', 'redis://localhost')).netloc,
    database=os.environ.get('REDIS_DATABASE', '0'))
CELERY_RESULT_BACKEND = 'redis://{host}/{database}'.format(
    host=urlparse(
        os.environ.get('REDIS_PORT', 'redis://localhost')).netloc,
    database=os.environ.get('REDIS_DATABASE', '0'))
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CACHE_TYPE = 'simple' if DEBUG else 'redis'
CACHE_REDIS_URL = 'redis://{host}/{database}'.format(
    host=urlparse(
        os.environ.get('REDIS_PORT', 'redis://localhost')).netloc,
    database=os.environ.get('REDIS_DATABASE', '0'))

LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'az': 'Azərbaycanca',
    'ar': 'العربية',
    'de': 'Deutsch',
    'ru': 'Русский',
}
BABEL_DEFAULT_LOCALE = os.environ.get('BABEL_DEFAULT_LOCALE', 'en')

ALLOWED_PUNCTUATIONS = '!'
CHARACTER_TRANSLATIONS = (
    ('i', '1'),
    ('I', '1'),
    ('o', '0'),
    ('O', '0'),
    ('l', '1'),
    ('L', '1'),
)
PUNCTUATIONS = filter(lambda s: s not in ALLOWED_PUNCTUATIONS,
                      string.punctuation) + ' '
TRANS_TABLE = dict((ord(char_from), ord(char_to))
                   for char_from, char_to in
                   CHARACTER_TRANSLATIONS)
MESSAGING_OUTGOING_GATEWAY = ast.literal_eval(
    os.environ.get('MESSAGING_OUTGOING_GATEWAY', '''{
        'type': 'kannel',
        'gateway_url': 'http://localhost:13013/cgi-bin/sendsms',
        'username': 'foo',
        'password': 'bar'
    }'''))
MESSAGING_CC = ast.literal_eval(os.environ.get('MESSAGING_CC', '[]'))
MESSAGING_SECRET = os.environ.get('MESSAGING_SECRET')

APPLICATIONS = ast.literal_eval(os.environ.get(
    'APPLICATIONS',
    '''("apollo.frontend",
        "apollo.locations",
        "apollo.participants",
        "apollo.formsframework",
        "apollo.submissions",
        "apollo.messaging",
        "apollo.process_analysis",
        "apollo.result_analysis",
        "apollo.odk")'''))

BIG_N = ast.literal_eval(os.environ.get('BIG_N', '0')) or numpy.inf
GOOGLE_ANALYTICS_KEY = os.environ.get('GOOGLE_ANALYTICS_KEY')
