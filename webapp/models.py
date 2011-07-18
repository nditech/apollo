from django.contrib.gis.db import models
from rapidsms.models import Contact
import datetime

class LocationType(models.Model):
    """Location Type"""
    name = models.CharField(max_length=100)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name

class Location(models.Model):
    """Location"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    type = models.ForeignKey(LocationType)
    parent = models.ForeignKey('Location')
    poly = models.PolygonField()
    latlon = models.PointField()

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ObserverRole(models.Model):
    """Roles"""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('ObserverRole')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name

#
#class Observer(models.Model):
#    """Election Observer"""
#    name = models.CharField(max_length=100)
#    observer_id = models.CharField(max_length=100)
#    contact = models.OneToOneField(Contact, blank=True, null=True)
#    email = models.EmailField(blank=True)
#    phone = models.CharField(max_length=100)
#    role = models.ForeignKey(ObserverRole)
#    location = models.ForeignKey(Location)
#    supervisor = models.ForeignKey('Observer')
#
#    class Admin:
#        list_display = ('',)
#        search_fields = ('',)
#
#    class Meta:
#        ordering = ['observer_id']
#
#    def __unicode__(self):
#        return self.name


class Checklist(models.Model):
    """A generic checklist"""
    location = models.ForeignKey(Location)
    observer = models.ForeignKey(Observer)
    date = models.DateField(default=datetime.datetime.today)
    comment = models.CharField(blank=True, max_length=100)
    created = models.DateTimeField(blank=False, auto_now_add=True)
    updated = models.DateTimeField(blank=False, auto_now=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

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
