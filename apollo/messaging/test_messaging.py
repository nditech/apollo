# -*- coding: utf-8 -*-
import pathlib
from datetime import datetime
from unittest import TestCase

import flask_babelex as babel
from flask_testing import TestCase as FlaskTestCase
from mimesis import Generic, locales

from apollo import services
from apollo.core import db, force_locale
from apollo.formsframework.models import Form
from apollo.messaging.helpers import lookup_participant
from apollo.messaging.utils import (
    get_unsent_codes, parse_responses, parse_text)
from apollo.testutils import factory, fixtures

DEFAULT_FIXTURES_PATH = pathlib.Path(__file__).parent / 'fixtures'


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class ResponseParserTest(TestCase):
    def setUp(self):
        f1 = AttributeDict(tag='AA', type='integer')
        f2 = AttributeDict(tag='BA', type='boolean')
        f3 = AttributeDict(tag='D', type='boolean')
        f4 = AttributeDict(tag='EA', type='multiselect')
        f5 = AttributeDict(tag='Comment1', type='comment')
        f6 = AttributeDict(tag='Comment2', type='comment')

        g1 = AttributeDict(name='Group 1')
        g1.fields = []
        g1.fields.append(f1)
        g1.fields.append(f2)
        g1.fields.append(f5)

        g2 = AttributeDict(name='Group 2')
        g2.fields = []
        g2.fields.append(f3)
        g2.fields.append(f4)
        g2.fields.append(f6)

        form = Form()
        form.data = {'groups': [g1, g2]}

        self.test_form = form

    def test_response_parsing(self):
        self.assertEqual(
            parse_responses('', self.test_form)[0],
            {})
        self.assertEqual(
            parse_responses('AA1BA2', self.test_form)[0],
            {'AA': '1', 'BA': 1})
        self.assertEqual(
            parse_responses('EA135DBAAA3', self.test_form)[0],
            {'AA': '3', 'BA': 1, 'D': 1, 'EA': '135'})
        self.assertNotIn('Comment1', parse_responses('EA135DBAAA3',
                         self.test_form)[0])

        self.assertEqual(
            parse_responses('ZX1CV2EA135DBAAA3', self.test_form)[0],
            {'AA': '3', 'BA': 1, 'D': 1, 'EA': '135', 'ZX': '1', 'CV': '2'})

    def test_leftover_processing(self):
        response_dict, extra = parse_responses(
            'ZX1CV2EA135DBAAA3', self.test_form)
        self.assertEqual(extra, '')

        response_dict, extra = parse_responses(
            'ZX1CV2EA135DBAAA3THIS IS A TEST', self.test_form)
        self.assertEqual(extra, 'THIS IS A TEST')

        response_dict, extra = parse_responses(
            'ZX1CV2EA135DBAAA3 THIS IS A TEST ', self.test_form)
        self.assertEqual(extra, 'THIS IS A TEST')


class MessagePartialTest(TestCase):
    def setUp(self):
        f1 = AttributeDict(tag='AA', type='integer')
        f2 = AttributeDict(tag='BA', type='integer')
        f3 = AttributeDict(tag='D', type='integer')
        f4 = AttributeDict(tag='EA', type='multiselect')
        f5 = AttributeDict(tag='Comment1', type='comment')
        f6 = AttributeDict(tag='Comment2', type='comment')

        g1 = AttributeDict(name='Group 1')
        g1.fields = []
        g1.fields.append(f1)
        g1.fields.append(f2)
        g1.fields.append(f5)

        g2 = AttributeDict(name='Group 2')
        g2.fields = []
        g2.fields.append(f3)
        g2.fields.append(f4)
        g2.fields.append(f6)

        form = Form()
        form.data = {'groups': [g1, g2]}

        self.test_form = form

    def test_partial_response(self):
        response_keys = ['AA', 'BA']
        self.assertEqual(
            get_unsent_codes(self.test_form, response_keys),
            ['Comment1']
        )

        response_keys = ['D', 'Comment2']
        self.assertEqual(
            get_unsent_codes(self.test_form, response_keys),
            ['EA']
        )

    def test_full_response(self):
        response_keys = ['AA', 'BA', 'Comment1']
        self.assertIsNone(get_unsent_codes(self.test_form, response_keys))


class MessageParsingTest(FlaskTestCase):
    def create_app(self):
        return factory.create_test_app()

    def test_parse_invalid_message(self):
        sample_text = '2014'
        result = parse_text(sample_text)
        (prefix, participant_id, exclamation, form_serial, responses,
            comment) = result

        self.assertIsNone(prefix)
        self.assertIsNone(participant_id, sample_text)
        self.assertIsNone(exclamation)
        self.assertIsNone(form_serial)
        self.assertIsNone(responses)
        self.assertIsNone(comment)

    def test_parse_survey_message(self):
        sample_text = 'TC111111X321AA2'
        result = parse_text(sample_text)
        (prefix, participant_id, exclamation, form_serial, responses,
            comment) = result

        self.assertEqual(prefix, 'TC')
        self.assertEqual(participant_id, '111111')
        self.assertFalse(exclamation)
        self.assertEqual(form_serial, '321')
        self.assertEqual(responses, 'AA2')
        self.assertIsNone(comment)

    def test_parse_comment_message(self):
        faker = Generic()

        # test with comments in the locales below
        # we're using Farsi instead of Arabic
        # as mimesis doesn't support Arabic yet ):
        for locale in ['EN', 'ES', 'FA', 'FR', 'RU']:
            current_locale = getattr(locales, locale)
            test_participant_id = faker.person.identifier('######')

            with self.subTest(current_locale=current_locale):
                with faker.text.override_locale(current_locale):
                    test_comment = faker.text.sentence()
                    sample_text = 'XA{}AA1AB2@{}'.format(
                        test_participant_id, test_comment)

                    result = parse_text(sample_text)
                    (prefix, participant_id, exclamation, form_serial,
                        responses, comment) = result

                    self.assertEqual(prefix, 'XA')
                    self.assertEqual(participant_id, test_participant_id)
                    self.assertFalse(exclamation)
                    self.assertEqual(responses, 'AA1AB2')
                    self.assertEqual(comment, test_comment)


class TranslationContextTestCase(FlaskTestCase):
    def create_app(self):
        return factory.create_test_app()

    def test_context_switching(self):
        d = datetime(2010, 4, 12, 13, 46)

        MESSAGES_EN = [
            'INCOMING',
            'OUTGOING',
            'Checklist Not Found',
            'Delivered',
        ]
        MESSAGES_FR = [
            'ENTRANT',
            'SORTANT',
            "Formulaire non trouvé",
            "Envoyé",
        ]
        MESSAGES_AR = [
            "الوارد",
            "الصادر",
            "قائمة التحقق غير موجودة",
            "تم التسليم",
        ]

        assert babel.format_datetime(d) == 'Apr 12, 2010, 1:46:00 PM'
        assert babel.format_date(d) == 'Apr 12, 2010'
        assert babel.format_time(d) == '1:46:00 PM'

        with force_locale('en'):
            assert babel.format_datetime(d) == 'Apr 12, 2010, 1:46:00 PM'
            assert babel.format_date(d) == 'Apr 12, 2010'
            assert babel.format_time(d) == '1:46:00 PM'
            for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_EN):
                assert babel.gettext(orig_msg) == trans_msg

        with force_locale('fr'):
            assert babel.format_datetime(d) == '12 avr. 2010 à 13:46:00'
            assert babel.format_date(d) == '12 avr. 2010'
            assert babel.format_time(d) == '13:46:00'
            for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_FR):
                assert babel.gettext(orig_msg) == trans_msg

        with force_locale('ar'):
            assert babel.format_datetime(d) == \
                '12\u200f/04\u200f/2010 1:46:00 م'
            assert babel.format_date(d) == '12\u200f/04\u200f/2010'
            assert babel.format_time(d) == '1:46:00 م'
            for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_AR):
                assert babel.gettext(orig_msg) == trans_msg


class ParticipantLookupTest(FlaskTestCase):
    fixtures_path = DEFAULT_FIXTURES_PATH / '417efb586ef.sql'

    def create_app(self):
        return factory.create_test_app()

    def setUp(self) -> None:
        db.create_all()

    def tearDown(self) -> None:
        db.session.close()
        db.drop_all()

    def test_lookup_nonexistent_participant(self):
        fixtures.load_sql_fixture(self.fixtures_path)
        participant_id = '111111'
        phone_number = '111111'
        message = f'AV{participant_id}'

        rv = lookup_participant(message, phone_number)
        self.assertIsNone(rv)
        event = services.events.fget_or_404(id=1)
        rv = lookup_participant(message, phone_number, event)
        self.assertIsNone(rv)

    def test_lookup_with_message(self):
        fixtures.load_sql_fixture(self.fixtures_path)
        participant_id = '403794'
        message = f'AV{participant_id}'
        phone_number = ''
        event1, event2, event3 = services.events.find().order_by('id').all()

        # participant doesn't exist in event1
        rv = lookup_participant(message, phone_number, event1)
        self.assertIsNone(rv)

        # participant in event2...
        rv = lookup_participant(message, phone_number, event2)
        self.assertEqual(rv.participant_id, participant_id)

        # ...is not the same as event3
        rv2 = lookup_participant(message, phone_number, event3)
        self.assertEqual(rv.participant_id, participant_id)
        self.assertNotEqual(rv.id, rv2.id)


    def test_lookup_with_number(self):
        fixtures.load_sql_fixture(self.fixtures_path)
        participant_id = '111111' # does not exist in any event
        phone_number = '7326767526' # exists in event2 and event3
        message = f'AA{participant_id}'
        event1, event2, event3 = services.events.find().order_by('id').all()

        # participant doesn't exist in event1
        rv = lookup_participant(message, phone_number, event1)
        self.assertIsNone(rv)

        # participant in event2...
        rv = lookup_participant(message, phone_number, event2)
        self.assertEqual(rv.phone_contacts[0].number, phone_number)

        # ...is not the same as event3
        rv2 = lookup_participant(message, phone_number, event3)
        self.assertEqual(rv2.phone_contacts[0].number, phone_number)
        self.assertNotEqual(rv.id, rv2.id)