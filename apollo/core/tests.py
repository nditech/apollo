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


@utils.override_settings(DEBUG=True)
class FormUtilsTest(MongoEngineTestCase):
    '''
    Tests for the core.utils.forms module
    '''
    def setUp(self):
        self.deployment = documents.Deployment(
            name='Deployment',
            hostnames=['localhost']
            ).save()
        event = documents.Event(
            deployment=self.deployment,
            name='Event').save()
        form_schema = {
            'name': 'Form ABC',
            'events': [event],
            'form_type': 'CHECKLIST',
            'prefix': 'ABC',
            'groups': [{
                'name': 'Group A',
                'fields': [{
                    'name': 'AA',
                    'description': 'Field AA',
                    'options': {'1': 'Option 1', '2': 'Option 2'},
                    'min_value': 1,
                    'max_value': 2,
                    'analysis_type': 'PROCESS'
                }]
            }, {
                'name': 'Group B',
                'fields': [{
                    'name': 'BA',
                    'description': 'Field BA',
                    'min_value': 0,
                    'max_value': 999,
                    'analysis_type': 'PROCESS'
                }, {
                    'name': 'BB',
                    'description': 'Field BB',
                    'min_value': 0,
                    'max_value': 9,
                    'analysis_type': 'PROCESS'
                }]
            }]
        }
        participant_schema = {
            'name': 'John Doe',
            'participant_id': '100001',
            'gender': 'M'
        }
        self.participant = documents.Participant(**participant_schema).save()
        self.form = documents.Form(**form_schema).save()

    def test_retrieve_form(self):
        from core.utils.forms import retrieve_form
        self.assertEqual(self.form, retrieve_form(self.deployment, 'ABC'))

    def test_build_questionnaire(self):
        from django import forms
        from core.utils.forms import build_questionnaire
        form = build_questionnaire(self.form)()

        self.assertIsNot(form.fields.get('AA', None), None)
        self.assertIs(form.fields.get('BC', None), None)

        self.assertIsInstance(form.fields.get('BA'), forms.IntegerField)
        self.assertEqual(form.fields.get('BA').max_value, 999)

    def test_form_validation(self):
        from core.utils.forms import build_questionnaire
        form_class = build_questionnaire(self.form)

        form = form_class({'DUMMY': None})
        self.assertFalse(form.is_valid())

        form = form_class({'prefix': 'ABC', 'participant': '100001'})
        self.assertTrue(form.is_valid())

        form = form_class({'prefix': 'ABC', 'participant': '101'})
        self.assertFalse(form.is_valid())

        form = form_class({'prefix': 'ABC',
                           'participant': '100001', 'comment': 'A comment',
                           'AA': '1', 'BA': '900', 'BB': '3'})
        self.assertTrue(form.is_valid())

        form = form_class({'prefix': 'ABC',
                           'participant': '100001', 'comment': 'A comment',
                           'AA': '3', 'BA': '900', 'BB': '3'})
        self.assertFalse(form.is_valid())
