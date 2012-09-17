"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from .models import *


class CoreTest(TestCase):
    def setUp(self):
        form1 = ExtensibleForm.objects.create(name='Form1', trigger='PSC')
        form2 = ExtensibleForm.objects.create(name='Form2', trigger='#')

        group1 = FormGroup.objects.create(form=form1)
        group2 = FormGroup.objects.create(form=form1)
        group3 = FormGroup.objects.create(form=form2, name='Default')

        field1 = FormField.objects.create(group=group1, name='field1', tag='AA')
        field2 = FormField.objects.create(group=group1, name='field2', tag='AB')
        field3 = FormField.objects.create(group=group1, name='field3', tag='AC')
        field4 = FormField.objects.create(group=group2, name='field4', tag='BA')
        field5 = FormField.objects.create(group=group2, name='field5', tag='BB')
        field6 = FormField.objects.create(group=group2, name='field6', tag='BC')

        field7 = FormField.objects.create(group=group3, name='field7',
            tag='YUM', present_true=True)

    def test_failed_parsing(self):
        '''Test what happens when parsing fails completely'''
        sample_text = 'Loop-de-loop'
        submission, remainder = ExtensibleForm.parse(sample_text)
        self.assertEqual(sample_text.lower(), remainder)
        self.assertEqual(submission, {})

    def test_complete_parsing(self):
        '''Tests what happens when parsing is complete, that is, no
        "leftover" text, and all fields have values'''
        sample_text = 'pscaa1ab2ac3ba1bb2bc3'
        submission, remainder = ExtensibleForm.parse(sample_text)
        self.assertEqual(remainder, '')
        self.assertNotEqual(submission, {})
        self.assertEqual(submission['AA'], 1)
        self.assertEqual(submission['AB'], 2)
        self.assertEqual(submission['AC'], 3)
        self.assertEqual(submission['BA'], 1)
        self.assertEqual(submission['BB'], 2)
        self.assertEqual(submission['BC'], 3)

    def test_incomplete_parsing(self):
        '''Tests what happens when parsing is incomplete'''
        sample_text = 'Jimmy Crocket ate the #1. It was yummy!'
        submission, remainder = ExtensibleForm.parse(sample_text)
        self.assertNotEqual('', remainder)
        self.assertNotEqual(submission, {})
        self.assertNotEqual(submission['YUM'], None)
        self.assertEqual(submission['YUM'], 1)
