from django.db import models
from rapidsms.contrib.locations.models import Location
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from rapidsms.models import Contact

class State(Location):
    name = models.CharField(max_length=100)
    code = models.CharField("State Code", max_length=50)

    @property
    def label(self):
        return self.name

class District(Location):
    name = models.CharField(max_length=100)
    code = models.CharField("Senatorial District Code", max_length=50)

    @property
    def label(self):
        return self.name

class LGA(Location):
    name = models.CharField(max_length=100)
    code = models.CharField("LGA Code", max_length=50)

    @property
    def label(self):
        return self.name

class RegistrationCenter(Location):
    name = models.CharField(max_length=100)
    code = models.CharField("Registration Center Code", max_length=50)

    @property
    def label(self):
        return self.name

class Observer(models.Model):
    contact = models.OneToOneField(Contact)
    observer_id = models.CharField(max_length=6)
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    supervisor = models.ForeignKey("Observer", related_name="observers", blank=True, null=True)

    def __set_name(self, name):
        self.contact.name = name

    def __get_name(self):
        return self.contact.name

    name = property(__get_name, __set_name)

    def __unicode__(self):
        return self.__get_name()

class VRChecklist(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField()
    A = models.IntegerField(blank=True, null=True)
    B = models.NullBooleanField(blank=True)
    C = models.IntegerField(blank=True, null=True)
    D1 = models.NullBooleanField(blank=True)
    D2 = models.NullBooleanField(blank=True)
    D3 = models.NullBooleanField(blank=True)
    D4 = models.NullBooleanField(blank=True)
    E1 = models.NullBooleanField(blank=True)
    E2 = models.NullBooleanField(blank=True)
    E3 = models.NullBooleanField(blank=True)
    E4 = models.NullBooleanField(blank=True)
    E5 = models.NullBooleanField(blank=True)
    F = models.IntegerField(blank=True, null=True)
    G = models.NullBooleanField(blank=True)
    H = models.IntegerField(blank=True, null=True)
    J = models.IntegerField(blank=True, null=True)
    K = models.IntegerField(blank=True, null=True)
    M = models.IntegerField(blank=True, null=True)
    N = models.IntegerField(blank=True, null=True)
    P = models.IntegerField(blank=True, null=True)
    Q = models.IntegerField(blank=True, null=True)
    R = models.IntegerField(blank=True, null=True)
    S = models.IntegerField(blank=True, null=True)
    T = models.NullBooleanField(blank=True)
    U = models.NullBooleanField(blank=True)
    V = models.NullBooleanField(blank=True)
    W = models.NullBooleanField(blank=True)
    X = models.NullBooleanField(blank=True)
    Y = models.IntegerField(blank=True, null=True)
    Z = models.IntegerField(blank=True, null=True)
    AA = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "VR Checklist for %s from %s on %s" % (self.location, self.observer, self.date)

class VRIncident(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField()
    A = models.NullBooleanField(blank=True)
    B = models.NullBooleanField(blank=True)
    C = models.NullBooleanField(blank=True)
    D = models.NullBooleanField(blank=True)
    E = models.NullBooleanField(blank=True)
    F = models.NullBooleanField(blank=True)
    G = models.NullBooleanField(blank=True)
    H = models.NullBooleanField(blank=True)
    J = models.NullBooleanField(blank=True)
    K = models.NullBooleanField(blank=True)
    M = models.NullBooleanField(blank=True)
    N = models.NullBooleanField(blank=True)
    P = models.NullBooleanField(blank=True)
    Q = models.NullBooleanField(blank=True)
    comment = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "VR Incident for %s from %s on %s" % (self.location, self.observer, self.date)

class DCOChecklist(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField()
    A = models.NullBooleanField(blank=True)
    B = models.NullBooleanField(blank=True)
    C = models.IntegerField(blank=True, null=True)
    D = models.NullBooleanField(blank=True)
    E = models.NullBooleanField(blank=True)
    F1 = models.NullBooleanField(blank=True)
    F2 = models.NullBooleanField(blank=True)
    F3 = models.NullBooleanField(blank=True)
    F4 = models.NullBooleanField(blank=True)
    F5 = models.NullBooleanField(blank=True)
    F6 = models.NullBooleanField(blank=True)
    F7 = models.NullBooleanField(blank=True)
    F8 = models.NullBooleanField(blank=True)
    F9 = models.NullBooleanField(blank=True)
    G = models.IntegerField(blank=True, null=True)
    H = models.NullBooleanField(blank=True)
    J = models.IntegerField(blank=True, null=True)
    K = models.IntegerField(blank=True, null=True)
    M = models.NullBooleanField(blank=True)
    N = models.NullBooleanField(blank=True)
    P = models.NullBooleanField(blank=True)
    Q = models.NullBooleanField(blank=True)
    R = models.NullBooleanField(blank=True)
    S = models.IntegerField(blank=True, null=True)
    T = models.IntegerField(blank=True, null=True)
    U = models.IntegerField(blank=True, null=True)
    V = models.IntegerField(blank=True, null=True)
    W = models.IntegerField(blank=True, null=True)
    X = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "DCO Checklist for %s from %s on %s" % (self.location, self.observer, self.date)

class DCOIncident(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField()
    A = models.NullBooleanField(blank=True)
    B = models.NullBooleanField(blank=True)
    C = models.NullBooleanField(blank=True)
    D = models.NullBooleanField(blank=True)
    E = models.NullBooleanField(blank=True)
    F = models.NullBooleanField(blank=True)
    G = models.NullBooleanField(blank=True)
    H = models.NullBooleanField(blank=True)
    J = models.NullBooleanField(blank=True)
    K = models.NullBooleanField(blank=True)
    comment = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "DCO Incident for %s from %s on %s" % (self.location, self.observer, self.date)

