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

