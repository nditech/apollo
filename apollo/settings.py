# -*- coding: utf-8 -*-
import ast
import os
from urlparse import urlparse

SECRET_KEY = os.environ.get('SECRET_KEY', 'SOMETHING_SECURE')
DEBUG = ast.literal_eval(
    os.environ.get('DEBUG', 'False'))
PAGE_SIZE = 25

if os.environ.get('container') == 'lxc':
    MONGO_ENV_NAME = 'MONGODB_PORT'
else:
    MONGO_ENV_NAME = 'MONGO_DATABASE_HOST'

MONGODB_SETTINGS = {
    'DB': os.environ.get('MONGO_DATABASE_NAME', 'apollo'),
    'HOST': urlparse(
        os.environ.get(MONGO_ENV_NAME, 'mongodb://localhost')).netloc
}

SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_URL_PREFIX = '/accounts'
SECURITY_LOGIN_USER_TEMPLATE = 'frontend/login_user.html'
SECURITY_EMAIL_SENDER = 'no-reply@apollo.la'
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True


LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'az': 'Azərbaycanca',
    'ar': 'العربية',
    'de': 'Deutsch',
}
