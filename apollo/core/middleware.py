# Middleware
from core.documents import Deployment


class DeploymentMiddleware(object):
    '''Middleware for connecting to the appropriate database before
    executing queries.'''

    def process_request(self, request):
        deployment = Deployment.objects.get(
            hostnames=request.META.get('HTTP_HOST'))
        if deployment:
            request.deployment = deployment

        return None
