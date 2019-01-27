# -*- coding: utf-8 -*-
from unittest import TestCase

from flask_testing import TestCase as FlaskTestCase
from mimesis import Generic, locales

from apollo.formsframework.models import Form
from apollo.messaging.utils import (
    get_unsent_codes, parse_responses, parse_text)
from apollo.testutils.factory import create_test_app


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
        return create_test_app()

    def test_parse_invalid_message(self):
        sample_text = '2014'
        prefix, participant_id, exclamation, responses, comment = parse_text(
            sample_text)

        self.assertIsNone(prefix)
        self.assertIsNone(participant_id, sample_text)
        self.assertIsNone(exclamation)
        self.assertIsNone(responses)
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
                    (prefix, participant_id, exclamation, responses,
                        comment) = result

                    self.assertEqual(prefix, 'XA')
                    self.assertEqual(participant_id, test_participant_id)
                    self.assertFalse(exclamation)
                    self.assertEqual(responses, 'AA1AB2')
                    self.assertEqual(comment, test_comment)
