from core import documents
from core.middleware import DeploymentMiddleware
from core.utils.test import MongoEngineTestCase
from django.test import utils
from django.test.client import RequestFactory


@utils.override_settings(DEBUG=True)
class DeploymentTest(MongoEngineTestCase):
    '''
    Tests for the DeploymentMiddleware
    '''

    def test_deploymentmiddleware(self):
        host_a = documents.Deployment(
            name='host_a', database='test_host_a', hostnames=['hosta.host'])
        host_a.save()
        host_b = documents.Deployment(
            name='host_b', database='test_host_b', hostnames=['hostb.host'])
        host_b.save()

        # Store 10 documents in host_a's database
        for i in range(10):
            documents.Event(name='Event {}'.format(i),
                            deployment=host_a).save()

        middleware = DeploymentMiddleware()
        factory = RequestFactory()

        request = factory.get('/')  # Simulate a GET request
        request.META['HTTP_HOST'] = 'hosta.host'
        self.assertEqual(middleware.process_request(request), None)
        self.assertEqual(
            documents.Event.objects.filter(deployment=request.deployment)
            .count(), 10)

        request.META['HTTP_HOST'] = 'hostb.host'
        self.assertEqual(middleware.process_request(request), None)
        self.assertEqual(
            documents.Event.objects.filter(deployment=request.deployment)
            .count(), 0)
