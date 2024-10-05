from depot.manager import DepotManager
from werkzeug.middleware.proxy_fix import ProxyFix

from apollo import create_app

application, celery = create_app()
application.app_context().push()

proxy_count = application.config["UPSTREAM_PROXY_COUNT"]

if DepotManager._middleware is None:
    application.wsgi_app = DepotManager.make_middleware(application.wsgi_app)

if proxy_count > 0:
    application.wsgi_app = ProxyFix(application.wsgi_app, x_for=proxy_count)
