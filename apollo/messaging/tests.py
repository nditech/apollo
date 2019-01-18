# -*- coding: utf-8 -*-
from unittest import TestCase
from apollo.formsframework.models import Form
from .utils import get_unsent_codes, parse_responses


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
