from django.db import models
from rapidsms.models import Contact
from utility_models import *
import datetime

'''
The Observer model has evolved into becoming an extension for
the RapidSMS contact model. Details are in extensions/rapidsms/contact.py
'''

class Checklist(models.Model):
    """A generic checklist"""
    location = models.ForeignKey(Location)
    observer = models.ForeignKey(Contact)
    date = models.DateField(default=datetime.datetime.today)
    comment = models.CharField(blank=True, max_length=100)
    created = models.DateTimeField(blank=False, auto_now_add=True)
    updated = models.DateTimeField(blank=False, auto_now=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)
    
    class Meta:
        permissions = (
            ('view_checklist', 'Can view checklist'),
        )

    def __unicode__(self):
        return self.id


class ChecklistForm(models.Model):
    """Checklist Form"""
    prefix = models.CharField(blank=True, max_length=100)
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ChecklistQuestionType(models.Model):
    """Checklist Question Type"""
    WIDGET_CHOICES = (
        ('select', 'drop down selection'),
        ('radio', 'radio button selection'),
        ('checkbox', 'checkbox multiple choice selection'),
        ('text', 'text input'),
    )
    name = models.CharField(max_length=100)
    widget = models.CharField(max_length=100, choices=WIDGET_CHOICES)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ChecklistQuestion(models.Model):
    """Checklist Question"""
    form = models.ForeignKey(ChecklistForm)
    type = models.ForeignKey(ChecklistQuestionType)
    code = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    weight = models.IntegerField(help_text='The order in which the question should be displayed')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.code


class ChecklistQuestionOption(models.Model):
    """Checklist Question Option"""
    question = models.ForeignKey(ChecklistQuestion, related_name='options')
    code = models.CharField(max_length=100, help_text='The option value for the question')
    name = models.CharField(max_length=100, help_text='The option text for the question')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ChecklistResponse(models.Model):
    """Checklist Response"""
    checklist = models.ForeignKey(Checklist, related_name='responses')
    question = models.ForeignKey(ChecklistQuestion)
    response = models.CharField(blank=True, max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.response


class IncidentForm(models.Model):
    """Incident Form"""
    prefix = models.CharField(blank=True, max_length=100)
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class IncidentResponse(models.Model):
    """Incident Type"""
    form = models.ForeignKey(IncidentForm)
    code = models.CharField(max_length=10)
    text = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.code


class Incident(models.Model):
    """Incident forms"""
    location = models.ForeignKey(Location)
    observer = models.ForeignKey(Contact)
    date = models.DateField(default=datetime.datetime.today)
    comment = models.CharField(blank=True, max_length=100)
    responses = models.ManyToManyField(IncidentResponse, related_name='incidents')
    created = models.DateTimeField(blank=False, auto_now_add=True)
    updated = models.DateTimeField(blank=False, auto_now=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.id
