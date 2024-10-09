from prettyconf import config

ATTACHMENTS_USE_S3 = False
DATABASE_NAME = config("DATABASE_NAME", default="apollo_testing")
SENTRY_DSN = None
PREFERRED_URL_SCHEME = "https"
