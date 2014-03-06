from core import documents
from core.utils.test import MongoEngineTestCase
from django.test import utils


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
