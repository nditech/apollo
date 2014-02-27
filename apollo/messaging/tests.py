from core.utils.test import MongoEngineTestCase
from django.test import utils


@utils.override_settings(DEBUG=True)
class MessagingTest(MongoEngineTestCase):
    def test_parse_text(self):
        from messaging.utils import parse_text
        self.assertEqual(
            parse_text('ABC101AA1BA2'),
            ('ABC', '101', 'CHECKLIST', 'AA1BA2', None))
        self.assertEqual(
            parse_text('ABC101!ABC'),
            ('ABC', '101', 'INCIDENT', 'ABC', None))
        self.assertEqual(
            parse_text('ABC101AA1BA2@with a comment'),
            ('ABC', '101', 'CHECKLIST', 'AA1BA2', 'with a comment'))
        self.assertEqual(
            parse_text('ABC101'),
            ('ABC', '101', 'CHECKLIST', None, None))
        self.assertEqual(
            parse_text('ABC101@with a comment'),
            ('ABC', '101', 'CHECKLIST', None, 'with a comment'))
        self.assertEqual(
            parse_text('ABC'),
            (None, None, None, None, None))
        self.assertEqual(
            parse_text(''),
            (None, None, None, None, None))
        self.assertEqual(
            parse_text('@with a comment'),
            (None, None, None, None, 'with a comment'))

    def test_parse_responses(self):
        from messaging.utils import parse_responses
        self.assertEqual(
            parse_responses('AA1BA2CA200', 'CHECKLIST'),
            {'AA': '1', 'BA': '2', 'CA': '200'})
        self.assertEqual(
            parse_responses('ABCDEF', 'INCIDENT'),
            {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1})
        self.assertEqual(
            parse_responses('', 'CHECKLIST'),
            {})
        self.assertEqual(
            parse_responses('', 'INCIDENT'),
            {})
        self.assertEqual(
            parse_responses('AA1BEA', 'CHECKLIST'),
            {'AA': '1', 'BEA': ''})
        self.assertEqual(
            parse_responses('AA1BEA2', 'INCIDENT'),
            {'A': 1, 'B': 1, 'E': 1})
