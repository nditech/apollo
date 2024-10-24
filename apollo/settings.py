# -*- coding: utf-8 -*-
import os
import string
from datetime import timedelta
from importlib import metadata
from pathlib import Path

import git
from flask_security import uia_username_mapper
from numpy import inf
from prettyconf import config

APPLICATIONS = (
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
    "apollo.odk",
)

VERSION = metadata.version("apollo")
try:
    repo = git.Repo(search_parent_directories=True)
    COMMIT = repo.head.object.hexsha[:8]
except (git.exc.InvalidGitRepositoryError, git.exc.GitCommandNotFound):
    COMMIT = config("COMMIT", default="")

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

try:
    SECRET_KEY = config("SECRET_KEY")
except KeyError:
    raise KeyError("A SECRET_KEY value must be defined in the environment.") from None

PAGE_SIZE = config("PAGE_SIZE", cast=int, default=25)
API_PAGE_SIZE = config("API_PAGE_SIZE", cast=int, default=100)

# default to UTC for prior deployments
TIMEZONE = config("TIMEZONE", default="UTC")

SERVER_NAME = config("SERVER_NAME", default=None)
APPLICATION_ROOT = config("APPLICATION_ROOT", default="/")
PREFERRED_URL_SCHEME = config("PREFERRED_URL_SCHEME", default="https")

ENABLE_MOE = config("ENABLE_MOE", cast=config.boolean, default=True)
X_FRAME_OPTIONS = config("X_FRAME_OPTIONS", default="DENY")

# This setting informs the application server of the number of
# upstream proxies to account for. Useful to determining true IP address
# for the request and preventing spoofing. Because this application is
# designed to be run behind a proper webserver, the default is set to 1
UPSTREAM_PROXY_COUNT = config("UPSTREAM_PROXY_COUNT", cast=int, default=1)

SENTRY_DSN = config("SENTRY_DSN", default=None)
SENTRY_USER_ATTRS = ["email"]

MAIL_SERVER = config("MAIL_SERVER", default=None)
MAIL_PORT = config("MAIL_PORT", default=None)
MAIL_USE_TLS = config("MAIL_USE_TLS", cast=config.boolean, default=False)
MAIL_USE_SSL = config("MAIL_USE_SSL", cast=config.boolean, default=False)
MAIL_USERNAME = config("MAIL_USERNAME", default=None)
MAIL_PASSWORD = config("MAIL_PASSWORD", default=None)
DEFAULT_EMAIL_SENDER = config("DEFAULT_EMAIL_SENDER", default="root@localhost")

REDIS_HOSTNAME = config("REDIS_HOSTNAME", default="redis")
REDIS_DATABASE = config("REDIS_DATABASE", default="0")

CELERY = {
    "broker_url": f"redis://{REDIS_HOSTNAME}/{REDIS_DATABASE}",
    "result_backend": f"redis://{REDIS_HOSTNAME}/{REDIS_DATABASE}",
    "task_track_started": True,
    "enable_utc": True,
    "timezone": TIMEZONE,
    "worker_send_task_events": True,
    "broker_connection_retry_on_startup": True,
}

CACHE_TYPE = "simple"
CACHE_REDIS_URL = f"redis://{REDIS_HOSTNAME}/{REDIS_DATABASE}"

LANGUAGES = {
    "ar": "العربية",
    "az": "Azərbaycanca",
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "ka": "ქართული",
    "ne": "नेपाली",
    "ro": "Română",
    "ru": "Русский",
    "si": "සිංහල",
    "sr": "srpski jezik",
    "ta": "தமிழ்",
}
BABEL_DEFAULT_LOCALE = config("BABEL_DEFAULT_LOCALE", default="en")

ALLOWED_PUNCTUATIONS = "!"
CHARACTER_TRANSLATIONS = (
    ("i", "1"),
    ("I", "1"),
    ("o", "0"),
    ("O", "0"),
    ("l", "1"),
    ("L", "1"),
)
PUNCTUATIONS = [s for s in string.punctuation if s not in ALLOWED_PUNCTUATIONS] + [" "]
TRANS_TABLE = {ord(char_from): ord(char_to) for char_from, char_to in CHARACTER_TRANSLATIONS}

MESSAGING_OUTGOING_GATEWAY = {}
_gateway_types = {"kannel": "kannel", "telerivet": "telerivet"}
_gateway_type = config("MESSAGING_OUTGOING_GATEWAY_TYPE", default="kannel", cast=config.option(_gateway_types))

MESSAGING_OUTGOING_GATEWAY["type"] = _gateway_type

if _gateway_type == _gateway_types["kannel"]:
    MESSAGING_OUTGOING_GATEWAY["gateway_url"] = config(
        "MESSAGING_OUTGOING_GATEWAY_URL", default="http://localhost:13013/cgi-bin/sendsms"
    )
    MESSAGING_OUTGOING_GATEWAY["username"] = config("MESSAGING_OUTGOING_GATEWAY_USERNAME", default="")
    MESSAGING_OUTGOING_GATEWAY["password"] = config("MESSAGING_OUTGOING_GATEWAY_PASSWORD", default="")
    MESSAGING_OUTGOING_GATEWAY["from"] = config("MESSAGING_OUTGOING_GATEWAY_SENDER", default="")
    MESSAGING_OUTGOING_GATEWAY["smsc"] = config("MESSAGING_OUTGOING_GATEWAY_SMSC", default=None)
    MESSAGING_OUTGOING_GATEWAY["charset"] = config("MESSAGING_OUTGOING_GATEWAY_CHARSET", default=None)
    MESSAGING_OUTGOING_GATEWAY["coding"] = config("MESSAGING_OUTGOING_GATEWAY_CODING", default=None)

elif _gateway_type == _gateway_types["telerivet"]:
    _project_id = config("MESSAGING_OUTGOING_GATEWAY_PROJECT_ID")
    MESSAGING_OUTGOING_GATEWAY["gateway_url"] = f"https://api.telerivet.com/v1/projects/{_project_id}/messages/send"
    MESSAGING_OUTGOING_GATEWAY["api_key"] = config("MESSAGING_OUTGOING_GATEWAY_API_KEY")
    MESSAGING_OUTGOING_GATEWAY["route_id"] = config("MESSAGING_OUTGOING_GATEWAY_ROUTE_ID", default=None)
    MESSAGING_OUTGOING_GATEWAY["priority"] = config("MESSAGING_OUTGOING_GATEWAY_PRIORITY", default=None)

MESSAGING_CC = config("MESSAGING_CC", cast=config.tuple, default=())
MESSAGING_SECRET = config("MESSAGING_SECRET", default=None)

BIG_N = config("BIG_N", cast=int, default=0) or inf
GOOGLE_ANALYTICS_KEY = config("GOOGLE_ANALYTICS_KEY", default=None)
GOOGLE_TAG_MANAGER_KEY = config("GOOGLE_TAG_MANAGER_KEY", default=None)

TRANSLATE_CHARS = config("TRANSLATE_CHARS", cast=config.boolean, default=True)
TRANSLITERATE_INPUT = config("TRANSLITERATE_INPUT", cast=config.boolean, default=False)
TRANSLITERATE_OUTPUT = config("TRANSLITERATE_OUTPUT", cast=config.boolean, default=False)

# SQLAlchemy settings
DATABASE_HOSTNAME = config("DATABASE_HOSTNAME", default="postgres")
DATABASE_USERNAME = config("DATABASE_USERNAME", default="postgres")
DATABASE_PASSWORD = config("DATABASE_PASSWORD", default="")
DATABASE_NAME = config("DATABASE_NAME", default="apollo")

# Flask-Upload settings
MAX_CONTENT_LENGTH = config("MAX_UPLOAD_SIZE_MB", cast=int, default=100) * 1024 * 1024  # 100 mb
DEFAULT_UPLOAD_PATH = os.path.join(PROJECT_ROOT, "uploads")
UPLOADS_DEFAULT_DEST = config("UPLOADS_DIR", default=DEFAULT_UPLOAD_PATH)

# Defines the secret to append to the /metrics/ endpoint
# to enable a prometheus exporter for metrics from the app
# if this is not defined, the exporter is disabled.
PROMETHEUS_SECRET = config("PROMETHEUS_SECRET", default="")

WEBPACK_MANIFEST_PATH = Path(PROJECT_ROOT, "apollo/static/dist/manifest.json")
WEBPACK_ASSETS_URL = "/static/dist/"

ENABLE_SOCIAL_LOGIN = config("ENABLE_SOCIAL_LOGIN", cast=config.boolean, default=False)

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")

FACEBOOK_CLIENT_ID = config("FACEBOOK_CLIENT_ID", default="")
FACEBOOK_CLIENT_SECRET = config("FACEBOOK_CLIENT_SECRET", default="")

MAPBOX_TOKEN = config("MAPBOX_TOKEN", default="")

API_KEY = config("API_KEY", default="")
REDIS_URL = f"redis://{REDIS_HOSTNAME}/{REDIS_DATABASE}"
KEEPALIVE_INTERVAL = 15  # in seconds

TASK_STATUS_TTL = config("TASK_STATUS_TTL", cast=int, default=300)  # in seconds

# attachment settings
BASE_UPLOAD_PATH = Path(config("DEFAULT_STORAGE_PATH", default=DEFAULT_UPLOAD_PATH))
IMAGE_UPLOAD_PATH = Path(config("IMAGES_STORAGE_PATH", default=BASE_UPLOAD_PATH.joinpath("images")))
ATTACHMENTS_USE_S3 = config("ATTACHMENTS_USE_S3", cast=config.boolean, default=False)

# WTF_CSRF_CHECK_DEFAULT = False

DEBUG = False
DEBUG_TB_ENABLED = False

_environment = os.environ.get("FLASK_ENV", "").lower()

if _environment == "development":
    from .development_settings import *  # noqa
elif _environment == "testing":
    from .testing_settings import *  # noqa
else:
    from .production_settings import *  # noqa

SQLALCHEMY_DATABASE_URI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}/{DATABASE_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECURITY_PASSWORD_HASH = "pbkdf2_sha256"
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = "/accounts"
SECURITY_USERNAME_ENABLE = True
SECURITY_POST_LOGOUT_VIEW = "/accounts/login"
SECURITY_LOGIN_USER_TEMPLATE = "frontend/login_user.html"
SECURITY_FORGOT_PASSWORD_TEMPLATE = "frontend/forgot_password.html"
SECURITY_RESET_PASSWORD_TEMPLATE = "frontend/reset_password.html"
SECURITY_EMAIL_SENDER = DEFAULT_EMAIL_SENDER
SECURITY_SEND_REGISTER_EMAIL = config("SECURITY_SEND_REGISTER_EMAIL", cast=config.boolean, default=False)
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SESSION_COOKIE_SECURE = True if PREFERRED_URL_SCHEME == "https" else False
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
SECURITY_USER_IDENTITY_ATTRIBUTES = [{"username": {"mapper": uia_username_mapper, "case_insensitive": True}}]
APOLLO_FIELD_COORDINATOR_EMAIL = config("APOLLO_FIELD_COORDINATOR_EMAIL", default="fc@example.com")
SECURITY_TWO_FACTOR = config("SECURITY_TWO_FACTOR", cast=config.boolean, default=False)
SECURITY_TOTP_ISSUER = config("SECURITY_TOTP_ISSUER")
TOTP_VERSION_TAG = config("TOTP_VERSION_TAG", default=None)
TOTP_SECRET = config("TOTP_SECRET", default=None)
SECURITY_TOTP_SECRETS = {TOTP_VERSION_TAG: TOTP_SECRET}
SECURITY_TWO_FACTOR_ENABLED_METHODS = config("SECURITY_TWO_FACTOR_ENABLED_METHODS", cast=config.list, default=["email", "sms"])

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID") if ATTACHMENTS_USE_S3 else None
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY") if ATTACHMENTS_USE_S3 else None
AWS_DEFAULT_REGION = config("AWS_DEFAULT_REGION", default=None)
AWS_DEFAULT_BUCKET = config("AWS_DEFAULT_BUCKET", default=None)
AWS_IMAGES_REGION = config("AWS_IMAGES_REGION", default=AWS_DEFAULT_REGION)
AWS_IMAGES_BUCKET = config("AWS_IMAGES_BUCKET", default=AWS_DEFAULT_BUCKET)
AWS_ENDPOINT_URL = config("AWS_ENDPOINT_URL", default=None)

# JWT settings
JWT_TOKEN_LOCATION = config("JWT_TOKEN_LOCATION", cast=config.tuple, default="cookies")
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default=SECRET_KEY)
JWT_ACCESS_TOKEN_EXPIRES = timedelta(
    seconds=config("JWT_ACCESS_TOKEN_LIFETIME_SECONDS", cast=int, default=(60 * 60 * 24 * 3))
)  # expires in 3 days
JWT_ERROR_MESSAGE_KEY = "message"
JWT_COOKIE_SECURE = SESSION_COOKIE_SECURE
JWT_ACCESS_COOKIE_PATH = "/api"

# PWA 2FA
PWA_TWO_FACTOR = config("PWA_TWO_FACTOR", cast=config.boolean, default=SECURITY_TWO_FACTOR)

# rate limiting settings
RATELIMIT_STORAGE_URI = REDIS_URL
