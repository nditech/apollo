from prettyconf import config

ATTACHMENTS_USE_S3 = False
FLASK_DEBUG = True
DEBUG = True
SENTRY_DSN = None
SQLALCHEMY_ECHO = config("SQLALCHEMY_ECHO", cast=config.boolean, default=True)
SSL_REQUIRED = False

# Flask-DebugToolbar settings
DEBUG_TB_ENABLED = config("DEBUG_TB_ENABLED", cast=config.boolean, default=True)
DEBUG_TB_INTERCEPT_REDIRECTS = False
DEBUG_TB_PROFILER_ENABLED = True
