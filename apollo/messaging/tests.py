# from core import documents
# from core.utils.test import MongoEngineTestCase
# from django.http import QueryDict
# from django.test import utils
# from django.test.client import RequestFactory


# @utils.override_settings(DEBUG=True)
# class MessagingTest(MongoEngineTestCase):
#     def setUp(self):
#         self.deployment = documents.Deployment(
#             name='Deployment',
#             hostnames=['localhost']
#             ).save()
#         event = documents.Event(
#             deployment=self.deployment,
#             name='Event').save()
#         form_schema = {
#             'name': 'Form ABC',
#             'events': [event],
#             'form_type': 'CHECKLIST',
#             'prefix': 'ABC',
#             'groups': [{
#                 'name': 'Group A',
#                 'fields': [{
#                     'name': 'AA',
#                     'description': 'Field AA',
#                     'options': {'1': 'Option 1', '2': 'Option 2'},
#                     'min_value': 1,
#                     'max_value': 2,
#                     'analysis_type': 'PROCESS'
#                 }]
#             }, {
#                 'name': 'Group B',
#                 'fields': [{
#                     'name': 'BA',
#                     'description': 'Field BA',
#                     'min_value': 0,
#                     'max_value': 999,
#                     'analysis_type': 'PROCESS'
#                 }, {
#                     'name': 'BB',
#                     'description': 'Field BB',
#                     'min_value': 0,
#                     'max_value': 9,
#                     'analysis_type': 'PROCESS'
#                 }]
#             }]
#         }
#         participant_schema = {
#             'name': 'John Doe',
#             'participant_id': '100001',
#             'gender': 'M'
#         }
#         self.participant = documents.Participant(**participant_schema).save()
#         self.form = documents.Form(**form_schema).save()

#     def test_parse_text(self):
#         from messaging.utils import parse_text
#         self.assertEqual(
#             parse_text('ABC101AA1BA2'),
#             ('ABC', '101', 'CHECKLIST', 'AA1BA2', None))
#         self.assertEqual(
#             parse_text('ABC101!ABC'),
#             ('ABC', '101', 'INCIDENT', 'ABC', None))
#         self.assertEqual(
#             parse_text('ABC101AA1BA2@with a comment'),
#             ('ABC', '101', 'CHECKLIST', 'AA1BA2', 'with a comment'))
#         self.assertEqual(
#             parse_text('ABC101'),
#             ('ABC', '101', 'CHECKLIST', None, None))
#         self.assertEqual(
#             parse_text('ABC101@with a comment'),
#             ('ABC', '101', 'CHECKLIST', None, 'with a comment'))
#         self.assertEqual(
#             parse_text('ABC'),
#             (None, None, None, None, None))
#         self.assertEqual(
#             parse_text(''),
#             (None, None, None, None, None))
#         self.assertEqual(
#             parse_text('@with a comment'),
#             (None, None, None, None, 'with a comment'))

#     def test_parse_responses(self):
#         from messaging.utils import parse_responses
#         self.assertEqual(
#             parse_responses('AA1BA2CA200', 'CHECKLIST'),
#             {'AA': '1', 'BA': '2', 'CA': '200'})
#         self.assertEqual(
#             parse_responses('ABCDEF', 'INCIDENT'),
#             {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1})
#         self.assertEqual(
#             parse_responses('', 'CHECKLIST'),
#             {})
#         self.assertEqual(
#             parse_responses('', 'INCIDENT'),
#             {})
#         self.assertEqual(
#             parse_responses('AA1BEA', 'CHECKLIST'),
#             {'AA': '1', 'BEA': ''})
#         self.assertEqual(
#             parse_responses('AA1BEA2', 'INCIDENT'),
#             {'A': 1, 'B': 1, 'E': 1})

#     def test_parse_message(self):
#         from messaging.forms import KannelForm
#         from messaging.views import parse_message
#         form = KannelForm({'sender': '123', 'text': 'ABC'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Invalid message: "ABC". Please check and resend!')

#         form = KannelForm({'sender': '123', 'text': 'ABC100001'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Invalid message: "ABC100001". Please check and resend!')

#         form = KannelForm({'sender': '123', 'text': 'ABC10001AA1@a comment'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Observer ID not found. Please resend with valid '
#             'Observer ID. You sent: ABC10001AA1@a comment')

#         form = KannelForm({'sender': '123', 'text': 'ABC100001EA1EC1'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Unknown question codes: "EA, EC". '
#             'You sent: ABC100001EA1EC1')

#         form = KannelForm({'sender': '123', 'text': 'ABC100001AA3BA1000'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Invalid response(s) for question(s):'
#             ' "AA, BA". You sent: ABC100001AA3BA1000')

#         form = KannelForm({'sender': '123', 'text': 'ABC100001AA1BA200@good'})
#         self.assertEqual(
#             parse_message(form, self.deployment),
#             'Thank you! Your report was received!'
#             ' You sent: ABC100001AA1BA200@good')

#     def test_kannel_backend(self):
#         from messaging.views import kannel_view
#         factory = RequestFactory()
#         request = factory.get('/')  # Simulate a GET request
#         request.META['HTTP_HOST'] = 'localhost'
#         request.deployment = self.deployment
#         request.GET = QueryDict('sender=123&text=ABC100001AA1BA200@good')

#         response = kannel_view(request)
#         self.assertEqual(response.content,
#                          'Thank you! Your report was received!'
#                          ' You sent: ABC100001AA1BA200@good')

#         request.GET = QueryDict('sender=123&text=ABC100001AA3BA1000')
#         response = kannel_view(request)
#         self.assertEqual(response.content,
#                          'Invalid response(s) for question(s):'
#                          ' "AA, BA". You sent: ABC100001AA3BA1000')

#     def test_telerivet_backend(self):
#         from messaging.views import telerivet_view
#         factory = RequestFactory()
#         request = factory.get('/')  # Simulate a GET request
#         request.META['HTTP_HOST'] = 'localhost'
#         request.deployment = self.deployment
#         request.POST = QueryDict(
#             'id=1&from_number=123&content=ABC100001AA1BA200@good')

#         response = telerivet_view(request)
#         self.assertEqual(response.content,
#                          '{"messages": [{"content": "Thank you! '
#                          'Your report was received! '
#                          'You sent: ABC100001AA1BA200@good"}]}')

#         request.POST = QueryDict(
#             'id=1&from_number=123&content=ABC100001AA3BA1000')
#         response = telerivet_view(request)
#         self.assertEqual(response.content,
#                          '{"messages": [{"content": "Invalid response(s) for '
#                          'question(s): \\"AA, BA\\". '
#                          'You sent: ABC100001AA3BA1000"}]}')
from unittest import TestCase
from apollo.formsframework.models import Form, FormGroup, FormField
from .utils import parse_responses


class ResponseParserTest(TestCase):
    def setUp(self):
        f1 = FormField(name='AA')
        f2 = FormField(name='BA', represents_boolean=True)
        f3 = FormField(name='D', represents_boolean=True)
        f4 = FormField(name='EA', allows_multiple_values=True)
        f5 = FormField(name='Comment1', is_comment_field=True)
        f6 = FormField(name='Comment2', is_comment_field=True)

        g1 = FormGroup()
        g1.fields.append(f1)
        g1.fields.append(f2)
        g1.fields.append(f5)

        g2 = FormGroup()
        g2.fields.append(f3)
        g2.fields.append(f4)
        g2.fields.append(f6)

        form = Form()
        form.groups.append(g1)
        form.groups.append(g2)

        self.test_form = form

    def test_response_parsing(self):
        self.assertEqual(
            parse_responses('', self.test_form),
            {})
        self.assertEqual(
            parse_responses('AA1BA2', self.test_form),
            {'AA': '1', 'BA': 1})
        self.assertEqual(
            parse_responses('EA135DBAAA3', self.test_form),
            {'AA': '3', 'BA': 1, 'D': 1, 'EA': '135'})
        self.assertNotIn('Comment1', parse_responses('EA135DBAAA3',
                         self.test_form))
