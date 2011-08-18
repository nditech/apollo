from django.db import models
from django.core.validators import RegexValidator
from rapidsms.models import Contact
from utility_models import *
import re
import datetime

'''
The Observer model has evolved into becoming an extension for
the RapidSMS contact model. Details are in extensions/rapidsms/contact.py
'''
class ChecklistForm(models.Model):
    """Checklist Form"""
    prefix = models.CharField(blank=True, max_length=100, validators=[RegexValidator(re.compile(r'[A-HJKMNP-Z]+', re.I), message='Prefixes may contain alphabets except the letters I, L and O')])
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class Checklist(models.Model):
    """A generic checklist"""
    form = models.ForeignKey(ChecklistForm, related_name='checklists')
    location = models.ForeignKey(Location, limit_choices_to={'type__name': 'Polling Stream'})
    observer = models.ForeignKey(Contact)
    date = models.DateField(default=datetime.datetime.today)
    comment = models.CharField(blank=True, max_length=200)
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
        return '%s -> %s' % (self.observer.observer_id, self.location)


class ChecklistResponse(models.Model):
    """Checklist Response"""
    # note that this model should only be subclassed once or else you'll have
    # problems with the related_name in the reverse fk relation.
    # please see https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    checklist = models.OneToOneField(Checklist, related_name='response')
    
    # In actual models inheriting from this, you define the questions below
    # A = models.IntegerField(blank=True, null=True, validators=[MaxValueValidator(2)],help_text='What time did the registration centre open? (tick one) (If the centre has not opened by 12 noon, complete a critical incident form and report immediately)')
    class Meta:
        abstract = True


class IncidentForm(models.Model):
    """Incident Form"""
    prefix = models.CharField(blank=True, max_length=100, validators=[RegexValidator(re.compile(r'[A-HJKMNP-Z]+', re.I), message='Prefixes may contain alphabets except the letters I, L and O')])
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class Incident(models.Model):
    """Incident forms"""
    form = models.ForeignKey(IncidentForm, related_name='incidents')
    location = models.ForeignKey(Location)
    observer = models.ForeignKey(Contact)
    date = models.DateField(default=datetime.datetime.today)
    comment = models.CharField(blank=True, max_length=100)
    created = models.DateTimeField(blank=False, auto_now_add=True)
    updated = models.DateTimeField(blank=False, auto_now=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return '%s (%s) -> %d' % (self.observer.observer_id, self.location, self.id)


class IncidentResponse(models.Model):
    """Incident Response"""
    # note that this model should only be subclassed once or else you'll have
    # problems with the related_name in the reverse fk relation.
    # please see https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    incident = models.OneToOneField(Incident, related_name='response')
    
    # In actual models inheriting from this, you define the questions below
    # A = models.IntegerField(blank=True, null=True, validators=[MaxValueValidator(2)],help_text='What time did the registration centre open? (tick one) (If the centre has not opened by 12 noon, complete a critical incident form and report immediately)')
    class Meta:
        abstract = True


class Election(models.Model):
    """Election contest type"""
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class Party(models.Model):
    """Political parties contesting for positions in the elections"""
    acronym = models.CharField(max_length=100)
    name = models.CharField(max_length=100, help_text='Political party name')
    # adding locations enables the distinction of parties contesting at different levels
    # a party contesting at the national elections may not be contesting at the guber level
    location = models.ForeignKey(Location, related_name='parties')
    elections = models.ManyToManyField(Election, related_name='parties')
    
    class Meta:
        verbose_name_plural = 'Parties'

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.acronym


class PartyVote(models.Model):
    """Stores votes for each party in a checklist"""
    party = models.ForeignKey(Party, related_name='votes')
    checklist = models.ForeignKey(Checklist, related_name='votes')
    votes = models.IntegerField(blank=True, null=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return "%s (%s) -> %d" % (self.party.acronym, self.checklist.id, self.votes)


class ChecklistFormParty(models.Model):
    """Parties contesting for a particular checklist form"""
    weight = models.IntegerField(help_text='The order in which the party should be displayed')
    form = models.ForeignKey(ChecklistForm, related_name='checklist_form_parties')
    party = models.ForeignKey(Party, related_name='checklist_form_parties')

    class Meta:
        verbose_name_plural = 'Checklist form parties'
        
    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return '%s -> %s' % (self.form, self.party)
