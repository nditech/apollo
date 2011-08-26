#from django.contrib.gis.db import models
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class LocationType(MPTTModel):
    """Location Type"""
    name = models.CharField(max_length=100)
    # code is used mainly in the SMS processing logic
    code = models.CharField(blank=True, max_length=10, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    in_form = models.BooleanField(default=False, db_index=True, help_text="Determines whether this LocationType can be used in SMS forms")

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class Location(MPTTModel):
    """Location"""
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=100, db_index=True)
    type = models.ForeignKey(LocationType)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    path = models.TextField(blank=True, help_text='SVG path data for location')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ObserverRole(models.Model):
    """Roles"""
    name = models.CharField(max_length=100, db_index=True)
    parent = models.ForeignKey('ObserverRole', null=True, blank=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name
