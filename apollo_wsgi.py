#!/usr/bin/env python
import os
import sys
import site

#SITE = '/path/to/site-packages'
#site.addsitedir(SITE)

os.environ["CELERY_LOADER"] = "django"

sys.path.append(os.path.join(os.path.dirname(__file__)))

from django.core.management import setup_environ
import settings
setup_environ(settings)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
