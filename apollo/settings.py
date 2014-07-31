# -*- coding: utf-8 -*-
import ast
from datetime import timedelta
import os
import string
from urlparse import urlparse

SECRET_KEY = os.environ.get('SECRET_KEY', 'SOMETHING_SECURE')
DEBUG = ast.literal_eval(
    os.environ.get('DEBUG', 'False'))
PAGE_SIZE = 25

MONGODB_SETTINGS = {
    'DB': os.environ.get('MONGO_DATABASE_NAME', 'apollo'),
    'HOST': urlparse(
        os.environ.get('MONGODB_PORT', 'mongodb://localhost')).netloc
}

SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = '/accounts'
SECURITY_LOGIN_USER_TEMPLATE = 'frontend/login_user.html'
SECURITY_EMAIL_SENDER = 'no-reply@apollo.la'
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SESSION_COOKIE_SECURE = ast.literal_eval(
    os.environ.get('SESSION_COOKIE_SECURE', 'False'))
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
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

FORCE_SSL = ast.literal_eval(
    os.environ.get('FORCE_SSL', 'False'))
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')

SENTRY_DSN = os.environ.get('SENTRY_DSN')

LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'az': 'Azərbaycanca',
    'ar': 'العربية',
    'de': 'Deutsch',
}

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

BIG_N = ast.literal_eval(os.environ.get('BIG_N', '60000'))
GOOGLE_ANALYTICS_KEY = os.environ.get('GOOGLE_ANALYTICS_KEY')
