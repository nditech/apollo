"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from .forms import generate_submission_form
from .models import *


class CoreTest(TestCase):
    test_form = None

    def setUp(self):
        form1 = Form.objects.create(name='Form1',
            trigger=r'^PSC\d{6}(?P<fields>([A-Z]+\d+)+)@?.*$',
            field_pattern='(?P<key>[A-Z]+)(?P<value>\d+)')
        form2 = Form.objects.create(name='Form2',
            trigger='#(?P<fields>([A-Z]{1})+)',
            field_pattern=r'(?P<key>[A-Z]{1})')

        self.test_form = form1

        group1 = FormGroup.objects.create(form=form1)
        group2 = FormGroup.objects.create(form=form1)
        group3 = FormGroup.objects.create(form=form2, name='Default')

        FormField.objects.create(group=group1, name='field1', tag='AA')
        FormField.objects.create(group=group1, name='field2', tag='AB')
        FormField.objects.create(group=group1, name='field3', tag='AC')
        FormField.objects.create(group=group2, name='field4', tag='BA')
        FormField.objects.create(group=group2, name='field5', tag='BB',
            lower_limit=0, upper_limit=15)
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
        self.assertEqual(submission['data']['AA'], '1')
        self.assertEqual(submission['data']['AB'], '2')
        self.assertEqual(submission['data']['AC'], '3')
        self.assertEqual(submission['data']['BA'], '1')
        self.assertEqual(submission['data']['BB'], '2')
        self.assertEqual(submission['data']['BC'], '2')

    def test_incomplete_parsing(self):
        '''Tests what happens when parsing is incomplete'''
        submission, _ = Form.parse('#YN')
        self.assertNotEqual(submission, {})
        self.assertNotEqual(submission['data']['Y'], None)
        self.assertEqual(submission['data']['Y'], '1')

    def test_form_validation(self):
        '''Tests the validation of fields and field values'''
        submission, _ = Form.parse('PSC111111AA1AB2AC3BA10000BB2BC3BD4')
        self.assertNotEqual(submission, {})
        self.assertEqual(submission['data']['AA'], '1')
        self.assertEqual(submission['data']['AB'], '2')
        self.assertEqual(submission['data']['AC'], '3')
        self.assertTrue('BA' not in submission)
        self.assertTrue('BA' in submission['range_error_fields'])
        self.assertEqual(submission['data']['BB'], '2')
        self.assertTrue('BC' not in submission)
        self.assertTrue('BC' in submission['range_error_fields'])
        self.assertTrue('BD' in submission['attribute_error_fields'])

    def test_form_generation(self):
        '''Tests the Django form generator'''
        form_class = generate_submission_form(self.test_form)
        t_form = form_class()

        self.assertEqual(len(t_form.fields), 6)
        self.assertTrue('AA' in t_form.fields)
        self.assertTrue('AB' in t_form.fields)
        self.assertTrue('BC' in t_form.fields)
        self.assertEqual(len(t_form.fields['BC'].choices), 2)
        self.assertEqual(len(t_form.fieldsets), 2)

    def test_form_validator(self):
        '''Tests that the generated form validates properly'''
        form_class = generate_submission_form(self.test_form)
        # should be invalid when bound because BB is limited to 0-15
        data = {'AA': '1', 'AB': '2', 'AC': '3', 'BB': '27', 'BC': '5'}
        t_form = form_class(data)

        self.assertEqual(t_form.is_valid(), False)
