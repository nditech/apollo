# Middleware
from core.documents import Deployment
from django.conf import settings
from mongoengine.connection import connect, disconnect


class DeploymentMiddleware(object):
    '''Middleware for connecting to the appropriate database before
    executing queries.'''

    def process_request(self, request):
        deployment = Deployment.objects.get(
            hostnames=request.META.get('HTTP_HOST'))
        if deployment:
            disconnect()
            connect(deployment.database, host=settings.MONGO_DATABASE_HOST)

        return None
