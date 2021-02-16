# -*- coding: utf-8 -*-
from datetime import timedelta
import os
from pathlib import Path
import string

import numpy
from prettyconf import config

VERSION = config('VERSION', default='v3.1.1')
COMMIT = config('COMMIT', default='')

postgres_password = Path('/run/secrets/postgres_password')
test_postgres_password = Path('/run/secrets/postgres_password')

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

config.starting_path = PROJECT_ROOT

try:
    SECRET_KEY = config('SECRET_KEY')
except KeyError:
    raise KeyError('A SECRET_KEY value must be defined in the environment.')

DEBUG = config('DEBUG', cast=config.boolean, default=False)
PAGE_SIZE = config('PAGE_SIZE', cast=int, default=25)
API_PAGE_SIZE = config('API_PAGE_SIZE', cast=int, default=100)

# default to UTC for prior deployments
TIMEZONE = config('TIMEZONE', default='UTC')

SSL_REQUIRED = config('SSL_REQUIRED', cast=config.boolean, default=True)
ENABLE_MOE = config('ENABLE_MOE', cast=config.boolean, default=True)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

# This setting informs the application server of the number of
# upstream proxies to account for. Useful to determining true IP address
# for the request and preventing spoofing. Because this application is
# designed to be run behind a proper webserver, the default is set to 1
UPSTREAM_PROXY_COUNT = config('UPSTREAM_PROXY_COUNT', cast=int, default=1)

SENTRY_DSN = config('SENTRY_DSN', default=None)
SENTRY_USER_ATTRS = ['email']

MAIL_SERVER = config('MAIL_SERVER', default=None)
MAIL_PORT = config('MAIL_PORT', default=None)
MAIL_USE_TLS = config('MAIL_USE_TLS', cast=config.boolean, default=False)
MAIL_USE_SSL = config('MAIL_USE_SSL', cast=config.boolean, default=False)
MAIL_USERNAME = config('MAIL_USERNAME', default=None)
MAIL_PASSWORD = config('MAIL_PASSWORD', default=None)
DEFAULT_EMAIL_SENDER = config('DEFAULT_EMAIL_SENDER', default='root@localhost')

SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = '/accounts'
SECURITY_POST_LOGOUT_VIEW = '/accounts/login'
SECURITY_LOGIN_USER_TEMPLATE = 'frontend/login_user.html'
SECURITY_FORGOT_PASSWORD_TEMPLATE = 'frontend/forgot_password.html'
SECURITY_RESET_PASSWORD_TEMPLATE = 'frontend/reset_password.html'
SECURITY_EMAIL_SENDER = DEFAULT_EMAIL_SENDER
SECURITY_SEND_REGISTER_EMAIL = config(
    'SECURITY_SEND_REGISTER_EMAIL', cast=config.boolean, default=False)
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SESSION_COOKIE_SECURE = True if SSL_REQUIRED else False
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
SECURITY_USER_IDENTITY_ATTRIBUTES = config(
    'USER_IDENTITY_ATTRIBUTES', cast=config.tuple,
    default=('email,username'))
APOLLO_FIELD_COORDINATOR_EMAIL = config(
    'APOLLO_FIELD_COORDINATOR_EMAIL', default='fc@example.com')

CELERY_BROKER_URL = 'redis://{host}/{database}'.format(
    host=config('REDIS_HOSTNAME', default='redis'),
    database=config('REDIS_DATABASE', default='0'))
CELERY_RESULT_BACKEND = 'redis://{host}/{database}'.format(
    host=config('REDIS_HOSTNAME', default='redis'),
    database=config('REDIS_DATABASE', default='0'))
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CACHE_TYPE = 'simple' if DEBUG else 'redis'
CACHE_REDIS_URL = 'redis://{host}/{database}'.format(
    host=config('REDIS_HOSTNAME', default='redis'),
    database=config('REDIS_DATABASE', default='0'))

LANGUAGES = {
    'ar': 'العربية',
    'az': 'Azərbaycanca',
    'de': 'Deutsch',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'ro': 'Română',
    'ru': 'Русский',
    'si': "සිංහල",
    'ta': 'தமிழ்',
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
PUNCTUATIONS = [
    s for s in string.punctuation if s not in ALLOWED_PUNCTUATIONS] + [' ']
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
    default='''(
        "apollo.deployments",
        "apollo.frontend",
        "apollo.locations",
        "apollo.participants",
        "apollo.formsframework",
        "apollo.submissions",
        "apollo.messaging",
        "apollo.process_analysis",
        "apollo.result_analysis",
        "apollo.sse",
        "apollo.pwa",
        "apollo.odk")''')

BIG_N = config('BIG_N', cast=int, default=0) or numpy.inf
GOOGLE_ANALYTICS_KEY = config('GOOGLE_ANALYTICS_KEY', default=None)
GOOGLE_TAG_MANAGER_KEY = config('GOOGLE_TAG_MANAGER_KEY', default=None)

TRANSLATE_CHARS = config('TRANSLATE_CHARS', cast=config.boolean, default=True)
TRANSLITERATE_INPUT = config(
    'TRANSLITERATE_INPUT', cast=config.boolean, default=False)
TRANSLITERATE_OUTPUT = config(
    'TRANSLITERATE_OUTPUT', cast=config.boolean, default=False)


# SQLAlchemy settings
DATABASE_DRIVER = config('DATABASE_DRIVER', default='postgresql')
DATABASE_HOSTNAME = config('DATABASE_HOSTNAME', default='postgres')
DATABASE_USERNAME = config('DATABASE_USERNAME', default='postgres')
if postgres_password.is_file():
    DATABASE_PASSWORD = postgres_password.open().read()
else:
    DATABASE_PASSWORD = config('DATABASE_PASSWORD', default='')
DATABASE_NAME = config('DATABASE_NAME', default='apollo')
SQLALCHEMY_DATABASE_URI = config(
    'DATABASE_URL',
    default="{driver}://{username}:{password}@{hostname}/{database}".format(
        driver=DATABASE_DRIVER,
        username=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        hostname=DATABASE_HOSTNAME,
        database=DATABASE_NAME
    ))
SQLALCHEMY_TRACK_MODIFICATIONS = False

# FDT settings
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Flask-Upload settings
MAX_CONTENT_LENGTH = config(
    'MAX_UPLOAD_SIZE_MB', cast=int, default=8) * 1024 * 1024
default_upload_path = os.path.join(PROJECT_ROOT, 'uploads')
UPLOADS_DEFAULT_DEST = config('UPLOADS_DIR', default=default_upload_path)
PROMETHEUS_SECRET = config('PROMETHEUS_SECRET', default='')

WEBPACK_MANIFEST_PATH = Path(
        PROJECT_ROOT, 'apollo/static/dist/manifest.json')
WEBPACK_ASSETS_URL = '/static/dist/'

# Test settings
TEST_DATABASE_DRIVER = config('TEST_DATABASE_DRIVER', default='postgresql')
TEST_DATABASE_HOSTNAME = config('TEST_DATABASE_HOSTNAME', default='postgres')
TEST_DATABASE_USERNAME = config('TEST_DATABASE_USERNAME', default='postgres')
if test_postgres_password.is_file():
    TEST_DATABASE_PASSWORD = postgres_password.open().read()
else:
    TEST_DATABASE_PASSWORD = config('TEST_DATABASE_PASSWORD', default='')
TEST_DATABASE_NAME = config('TEST_DATABASE_NAME', default='apollo')
TEST_DATABASE_URL = config(
    'TEST_DATABASE_URL',
    default="{driver}://{username}:{password}@{hostname}/{database}".format(
        driver=TEST_DATABASE_DRIVER,
        username=TEST_DATABASE_USERNAME,
        password=TEST_DATABASE_PASSWORD,
        hostname=TEST_DATABASE_HOSTNAME,
        database=TEST_DATABASE_NAME
    ))

ENABLE_SOCIAL_LOGIN = config(
    'ENABLE_SOCIAL_LOGIN', cast=config.boolean, default=False)

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')

FACEBOOK_CLIENT_ID = config('FACEBOOK_CLIENT_ID', default='')
FACEBOOK_CLIENT_SECRET = config('FACEBOOK_CLIENT_SECRET', default='')

MAPBOX_TOKEN = config('MAPBOX_TOKEN', default='')

API_KEY = config('API_KEY', default='')
REDIS_URL = 'redis://{host}/{database}'.format(
    host=config('REDIS_HOSTNAME', default='redis'),
    database=config('REDIS_DATABASE', default='0'))
KEEPALIVE_INTERVAL = 15  # in seconds

TASK_STATUS_TTL = config('TASK_STATUS_TTL', cast=int, default=300)  # seconds

# attachment settings
base_upload_path = Path(
    config('DEFAULT_STORAGE_PATH', default=default_upload_path))
image_upload_path = Path(
    config('IMAGES_STORAGE_PATH', default=base_upload_path.joinpath('images')))
ATTACHMENTS_USE_S3 = config(
    'ATTACHMENTS_USE_S3', cast=config.boolean, default=False)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID') if ATTACHMENTS_USE_S3 else None
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY') \
    if ATTACHMENTS_USE_S3 else None
AWS_DEFAULT_REGION = config('AWS_DEFAULT_REGION', default=None)
AWS_DEFAULT_BUCKET = config('AWS_DEFAULT_BUCKET', default=None)
AWS_IMAGES_REGION = config('AWS_IMAGES_REGION', default=AWS_DEFAULT_REGION)
AWS_IMAGES_BUCKET = config('AWS_IMAGES_BUCKET', default=AWS_DEFAULT_BUCKET)
AWS_ENDPOINT_URL = config('AWS_ENDPOINT_URL', default=None)

# JWT settings
JWT_TOKEN_LOCATION = config(
    'JWT_TOKEN_LOCATION', cast=config.tuple, default='cookies')
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ACCESS_TOKEN_EXPIRES = timedelta(
    seconds=config("JWT_ACCESS_TOKEN_LIFETIME_SECONDS", cast=int, default=3600)
)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(
    seconds=config(
        "JWT_REFRESH_TOKEN_LIFETIME_SECONDS", cast=int, default=86400)
)
JWT_ERROR_MESSAGE_KEY = 'message'
