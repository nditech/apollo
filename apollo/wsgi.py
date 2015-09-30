from werkzeug.contrib.fixers import ProxyFix
from apollo import create_app

application = create_app()
if application.config.get('UPSTREAM_PROXY_COUNT') > 0:
    application.wsgi_app = ProxyFix(application.wsgi_app)
