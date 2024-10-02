# -*- coding: utf-8 -*-
from depot.manager import DepotManager
from werkzeug.middleware.proxy_fix import ProxyFix

from apollo import create_app

application = create_app()

if DepotManager._middleware is None:
    application.wsgi_app = DepotManager.make_middleware(application.wsgi_app)

if application.config.get("UPSTREAM_PROXY_COUNT") > 0:
    application.wsgi_app = ProxyFix(application.wsgi_app)
