from django.db import models
from formbuilder.models import Form
from django_orm.postgresql import hstore
from mptt.models import MPTTModel, TreeForeignKey
from datetime import datetime


class LocationType(MPTTModel):
    """Location Type"""
    name = models.CharField(max_length=100)
    # code is used mainly in the SMS processing logic
    code = models.CharField(blank=True, max_length=10, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    in_form = models.BooleanField(default=False, db_index=True, help_text="Determines whether this LocationType can be used in SMS forms")

    def __unicode__(self):
        return self.name


class Location(MPTTModel):
    """Location"""
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=100, db_index=True)
    type = models.ForeignKey(LocationType)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    path = models.TextField(blank=True, help_text='SVG path data for location')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=50)

    def __unicode__(self):
        return self.abbr


class ObserverRole(models.Model):
    """Roles"""
    name = models.CharField(max_length=100, db_index=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        return self.name


class Observer(models.Model):
    """Election Observer"""
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unspecified'),
    )
    observer_id = models.CharField(max_length=100, null=True, blank=True)
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location, related_name="observers")
    supervisor = models.ForeignKey('self', null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER, db_index=True)
    partner = models.ForeignKey(Partner, null=True, blank=True)
    data = hstore.DictionaryField(db_index=True)

    objects = hstore.HStoreManager()

    class Meta:
        ordering = ['observer_id']

    def __unicode__(self):
        return getattr(self, 'observer_id', "")


class Submission(models.Model):
    form = models.ForeignKey(Form, related_name='submissions')
    observer = models.ForeignKey(Observer, blank=True, null=True)
    date = models.DateField(default=datetime.today())
    data = hstore.DictionaryField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = hstore.HStoreManager()

    def __unicode__(self):
        return u"%s -> %s" % (self.pk, self.location,)
