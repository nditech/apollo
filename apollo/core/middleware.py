# Middleware
from core.documents import Deployment


class DeploymentMiddleware(object):
    '''Middleware for connecting to the appropriate database before
    executing queries.'''

    def process_request(self, request):
        try:
            request.deployment = Deployment.objects.get(
                hostnames=request.META.get('HTTP_HOST'))
        except Deployment.DoesNotExist:
            request.deployment = None

        return None
