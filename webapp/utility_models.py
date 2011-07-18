#from django.contrib.gis.db import models
from django.db import models

class LocationType(models.Model):
    """Location Type"""
    name = models.CharField(max_length=100)
    # code is used mainly in the SMS processing logic
    code = models.CharField(blank=True, max_length=10)

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
    parent = models.ForeignKey('Location', null=True)
    #poly = models.PolygonField()
    #latlon = models.PointField()

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name


class ObserverRole(models.Model):
    """Roles"""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('ObserverRole', null=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return self.name
