"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from .models import *


class CoreTest(TestCase):
    def setUp(self):
        form1 = Form.objects.create(name='Form1',
            trigger=r'^PSC\d{6}(?P<fields>([A-Z]+\d+)+)@?.*$',
            field_pattern='(?P<key>[A-Z]+)(?P<value>\d+)')
        form2 = Form.objects.create(name='Form2',
            trigger='#(?P<fields>([A-Z]{1})+)',
            field_pattern=r'(?P<key>[A-Z]{1})')

        group1 = FormGroup.objects.create(form=form1)
        group2 = FormGroup.objects.create(form=form1)
        group3 = FormGroup.objects.create(form=form2, name='Default')

        FormField.objects.create(group=group1, name='field1', tag='AA')
        FormField.objects.create(group=group1, name='field2', tag='AB')
        FormField.objects.create(group=group1, name='field3', tag='AC')
        FormField.objects.create(group=group2, name='field4', tag='BA')
        FormField.objects.create(group=group2, name='field5', tag='BB')
        BC = FormField.objects.create(group=group2, name='field6', tag='BC')

        FormField.objects.create(group=group3, name='field7',
            tag='Y', present_true=True)

        FormFieldOption.objects.create(field=BC, description='Yes', option=1)
        FormFieldOption.objects.create(field=BC, description='No', option=2)

    def test_failed_parsing(self):
        '''Test what happens when parsing fails completely'''
        self.assertRaises(Form.DoesNotExist, Form.parse, 'Loop-de-loop')

    def test_complete_parsing(self):
        '''Tests what happens when parsing is complete, that is, no
        "leftover" text, and all fields have values'''
        submission, _ = Form.parse('psc111111aa1ab2ac3ba1bb2bc2')
        self.assertNotEqual(submission, {})
        self.assertEqual(submission['AA'], 1)
        self.assertEqual(submission['AB'], 2)
        self.assertEqual(submission['AC'], 3)
        self.assertEqual(submission['BA'], 1)
        self.assertEqual(submission['BB'], 2)
        self.assertEqual(submission['BC'], 2)

    def test_incomplete_parsing(self):
        '''Tests what happens when parsing is incomplete'''
        submission, _ = Form.parse('#YN')
        self.assertNotEqual(submission, {})
        self.assertNotEqual(submission['Y'], None)
        self.assertEqual(submission['Y'], 1)

    def test_form_validation(self):
        '''Tests the validation of fields and field values'''
        submission, _ = Form.parse('PSC111111AA1AB2AC3BA10000BB2BC3BD4')
        self.assertNotEqual(submission, {})
        self.assertEqual(submission['AA'], 1)
        self.assertEqual(submission['AB'], 2)
        self.assertEqual(submission['AC'], 3)
        self.assertTrue('BA' not in submission)
        self.assertTrue('BA' in submission['range_error_fields'])
        self.assertEqual(submission['BB'], 2)
        self.assertTrue('BC' not in submission)
        self.assertTrue('BC' in submission['range_error_fields'])
        self.assertTrue('BD' in submission['attribute_error_fields'])
