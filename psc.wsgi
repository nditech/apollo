#!/usr/bin/env python
from django.core.management import setup_environ
import settings
setup_environ(settings)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
