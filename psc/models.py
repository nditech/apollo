from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from rapidsms.models import Contact
from django.contrib.auth.models import User
from south.modelsinspector import add_introspection_rules
from audit_log.models import fields
from audit_log.models.managers import AuditLog
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from psc_helpers import model_attribute_cache as cache
from datetime import datetime

class Zone(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("Zone Code", max_length=50, blank=True, db_index=True)

    @property
    def label(self):
        return self.name

    def __unicode__(self):
        return self.name

class State(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("State Code", max_length=50, blank=True, db_index=True)
    parent = models.ForeignKey("Zone", related_name="states", blank=True, null=True)

    @property
    def label(self):
        return self.name
    
    @property
    @cache
    def contesting_codes(self):
        return self.contesting_set.all().values_list('code', flat=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class District(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("Senatorial District Code", max_length=50, blank=True, db_index=True)
    parent = models.ForeignKey("State", related_name="districts", blank=True, null=True)

    @property
    def label(self):
        return self.name

    def __unicode__(self):
        return self.name

class LGA(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("LGA Code", max_length=50, blank=True, db_index=True)
    parent = models.ForeignKey("District", related_name="lgas", blank=True, null=True)

    @property
    def label(self):
        return self.name

    def __unicode__(self):
        return self.name

class Ward(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("Ward Code", max_length=50, blank=True, db_index=True)
    parent = models.ForeignKey("LGA", related_name="wards", blank=True, null=True)

    @property
    def label(self):
        return self.name

    def __unicode__(self):
        return self.name

class RegistrationCenter(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField("Registration Center Code", max_length=50, db_index=True)
    inec_code = models.CharField("INEC Registration Center Code", max_length=50, blank=True, null=True)
    parent = models.ForeignKey("LGA", blank=True, null=True)

    @property
    def label(self):
        return self.name

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Partner(models.Model):
    name = models.CharField("Partner's name", max_length=100)
    code = models.CharField(max_length=10)

    def __unicode__(self):
        return self.code

class Sample(models.Model):
    """The Sample model groups locations into samples that are used for data analyses"""
    SAMPLES = (
        ('NATIONAL', 'NATIONAL'),
        ('STATE', 'STATE'),
        ('CONTROL', 'CONTROL'),
        ('TREATMENT', 'TREATMENT'),
        ('NASS', 'NASS'))
        
    sample = models.CharField(choices=SAMPLES, max_length=100, db_index=True)
    observer = models.ForeignKey('Observer', blank=True, null=True, related_name="sample")

    def __unicode__(self):
        return "%s -> %s" % (self.observer, self.sample)


class Observer(models.Model):
    ROLES = (
        ('NSC', 'National Steering Committee'),
        ('NS', 'National Secretariat'),
        ('ZC', 'Zonal Coordinator'),
        ('SC', 'State Coordinator'),
        ('SDC', 'State Deputy Coordinator'),
        ('LGA', 'LGA Supervisor'),
        ('OBS', 'Observer'))
    
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('X', 'Unknown'))

    contact = models.OneToOneField(Contact, blank=True, null=True)
    dob = models.DateField("Date of Birth", blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=14, null=True, blank=True)
    observer_id = models.CharField(max_length=6, db_index=True)
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    supervisor = models.ForeignKey("Observer", related_name="observers", blank=True, null=True)
    partner = models.ForeignKey("Partner", related_name="observers")
    role = models.CharField('Observer Role', max_length=3, choices=ROLES, blank=True)
    position = models.PositiveSmallIntegerField(default=1, help_text='This field identifies an observer per polling unit.')
    gender = models.CharField('Sex', max_length=1, choices=GENDER, blank=True, null=True)
    
    zone = models.ForeignKey('Zone', blank=True, null=True)
    state = models.ForeignKey('State', blank=True, null=True)
    district = models.ForeignKey('District', blank=True, null=True)
    lga = models.ForeignKey('LGA', blank=True, null=True)
    ps = models.ForeignKey('RegistrationCenter', blank=True, null=True)
    
    def __set_name(self, name):
        self.contact.name = name

    def __get_name(self):
        return self.contact.name

    name = property(__get_name, __set_name)

    def __unicode__(self):
        return self.observer_id
    
    class Meta:
        permissions = (
            ('view_observer', 'Can view observer'),
        )
        ordering = ['observer_id']
        
    @property
    @cache
    def twin(self):
        if self.role == 'OBS':
            try:
                return Observer.objects.get(location_id=self.location_id, location_type=self.location_type, position=1 if self.position==2 else 2, role=self.role)
            except Observer.DoesNotExist:
                pass
            except Observer.MultipleObjectsReturned:
                return Observer.objects.get(location_id=self.location_id, location_type=self.location_type, position=1 if self.position==2 else 2, observer_id=str(int(self.observer_id)+1) if self.position==1 else str(int(self.observer_id)-1),role=self.role)
        elif self.role == 'LGA':
            try:
                return Observer.objects.get(location_id=self.location_id, location_type=self.location_type, position=1 if self.position==2 else 2, role=self.role, observer_id=str(int(self.observer_id)-5) if self.position==2 else str(int(self.observer_id)+5))
            except Observer.DoesNotExist:
                pass

class VRChecklist(models.Model):
    OPENTIME = ((1, 'Open by 8AM (1)'),
                (2, 'Between 8AM & 10AM (2)'),
                (3, 'Between 10AM & 12 noon (3)'),
                (4, 'Not Open by 12 noon (4)'))
    TURNOVER = ((1, 'None'),
                (2, 'Few'),
                (3, 'Half'),
                (4, 'Most'),
                (5, 'All'))
    YES_NO = ((0, 'Unspecified'),
              (1, 'Yes'),
              (2, 'No'))
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField(db_index=True)
    A = models.IntegerField(blank=True, null=True, choices=OPENTIME, help_text='What time did the registration centre open? (tick one) (If the centre has not opened by 12 noon, complete a critical incident form and report immediately)')
    B = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Were you permitted to observe at the registration centre? (tick Yes or No) (If not permitted to observe, complete a critical incident form and immediately report)')
    C = models.IntegerField(blank=True, null=True, help_text='How many registration officers were at the registration centre? (enter number)')
    D1 = models.NullBooleanField(blank=True, help_text='Did the registration centre have a complete and functioning Direct Data Capture (DDC) system (tick all that applies)')
    D2 = models.NullBooleanField(blank=True)
    D3 = models.NullBooleanField(blank=True)
    D4 = models.NullBooleanField(blank=True)
    E1 = models.NullBooleanField(blank=True, help_text='Was the registration centre missing any of the following materials? (tick all that applies)')
    E2 = models.NullBooleanField(blank=True)
    E3 = models.NullBooleanField(blank=True)
    E4 = models.NullBooleanField(blank=True)
    E5 = models.NullBooleanField(blank=True)
    F = models.IntegerField(blank=True, null=True, help_text='How many political party agents were at the registration centre? (enter number)')
    G = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Were any security agents present at the registration centre? (tick Yes or No)')
    H = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was anyone permitted to register who appeared under 18 years old? (tick the one that applies best)')
    J = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was anyone permitted to register who had indelible ink on his/her finger meaning he/she had already registered? (tick the one that applies best)')
    K = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was anyone permitted to register who did not appear to be from the community? (tick the one that applies best)')
    M = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Were the fingers of successful registrants marked with indelible ink? (tick the one that applies best)')
    N = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Were photos taken of successful registrants? (tick the one that applies best)')
    P = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text="Were successful registrants issued with temporary voters' card? (tick the one that applies best)")
    Q = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Were the names of successful registrants entered into the Direct Data Capture (DDC) system? (tick the one that applies best)')
    R = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Were the names of successful registrants entered into the Manual Register of Voters (MRV) Form EC.1A? (tick the one that applies best)')
    S = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Did anyone successfully register for someone who was not present at the registration centre (i.e. proxy registration)? (tick the one that applies best)')
    T = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did the Direct Data Capture (DDC) system properly function throughout the day? (tick Yes or No)')
    U = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did the registration centre run out of materials during the day? (tick Yes or No)')
    V = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did the registration centre remain open until 5 pm? (tick Yes or No)')
    W = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text="Did anyone attempt to disrupt voters' registration at the centre? (tick Yes or No)")
    X = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did anyone attempt to intimidate or harass people in or around the centre? (tick Yes or No)')
    Y = models.IntegerField(blank=True, null=True, help_text='How many people registered during this day? (record number from Certificate of Completion of Daily Registration of Voters Form EC.1B(1)) (if not permited to record this figure enter "9999")')
    Z = models.IntegerField(blank=True, null=True, help_text='How many people so far (total to date) have registered at this centre according to the Manual Register of Voters (MRV) Form EC.1A? (enter number) (if not permitted to record this figure enter "9999")')
    AA = models.IntegerField(blank=True, null=True, help_text='How many people so far (total to date) have registered according to the DDC system? (enter number) (if not permitted to record this figure, enter "9999")')
    comment = models.CharField(max_length=200, blank=True)
    submitted = models.BooleanField(default=False, help_text="This field tracks if (even though already created), this report has been submitted by the reporter")
    report_rc = models.CharField(blank=True, null=True, max_length=100, help_text="Registration Center as supplied by the data entry operator")
    report_rcid = models.CharField(blank=True, null=True, max_length=50, help_text="Registration Center ID as supplied by the data entry operator")
    verified_second = models.BooleanField(default=False)
    verified_third = models.BooleanField(default=False)
    audit_log = AuditLog()

    def __unicode__(self):
        return "VR Checklist for %s from %s on %s" % (self.location, self.observer, self.date)
    
    class Meta:
        permissions = (
            ('view_vrchecklist', 'Can view vr checklist'),
        )

class VRIncident(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField(db_index=True)
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
    comment = models.CharField(max_length=200, blank=True)
    audit_log = AuditLog()

    def __unicode__(self):
        return "VR Incident for %s from %s on %s" % (self.location, self.observer, self.date)
    
    class Meta:
        permissions = (
            ('view_vrincident', 'Can view vr incident'),
        )

class DCOChecklist(models.Model):
    OPENTIME = ((1, 'Open by 8AM (1)'),
                (2, 'Between 8AM & 10AM (2)'),
                (3, 'Between 10AM & 12 noon (3)'),
                (4, 'Not Open by 12 noon (4)'))
    TURNOVER = ((1, 'None'), (2, 'Few'), (3, 'Half'),(4, 'Most'),(5, 'All'))
    YES_NO = ((0, 'Unspecified'),(1, 'Yes'),(2, 'No'))
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField(db_index=True)
    A = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Was the registration centre open? (tick Yes or No) (If not permitted to observe, complete a critical incident form and immediately report)')
    B = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Were you permitted to observe at the registration centre? (tick Yes or No) (If not permitted to observe, complete a critical incident form and immediately report)')
    C = models.IntegerField(blank=True, null=True, help_text='How many registration officers were at the registration centre? (enter number)')
    D = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Was the Preliminary Register of Voters (PRV) posted in a visible place for public scrutiny? (tick Yes or No)(If the PRV was not posted, complete a critical incident form and immediately report)')
    E = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did the election officials provide any instructions to people about how to make a claim or objection? (tick Yes or No)')
    F1 = models.NullBooleanField(blank=True,  help_text='Were any of the following forms missing? (tick all that applies)')
    F2 = models.NullBooleanField(blank=True)
    F3 = models.NullBooleanField(blank=True)
    F4 = models.NullBooleanField(blank=True)
    F5 = models.NullBooleanField(blank=True)
    F6 = models.NullBooleanField(blank=True)
    F7 = models.NullBooleanField(blank=True)
    F8 = models.NullBooleanField(blank=True)
    F9 = models.NullBooleanField(blank=True)
    G = models.IntegerField(blank=True, null=True, help_text='How many political party agents were at the registration centre? (enter number)')
    H = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Were any security agents present at the registration centre? (tick Yes or No)')
    J = models.IntegerField(blank=True, null=True, help_text='How many names are on the Preliminary Register of Voters (PRV) (enter number) (if you are not permitted to record this figure, enter "9999")')
    K = models.IntegerField(blank=True, null=True, help_text='How many people came to the registration centre to scrutinize the Preliminary Register of Voters (PRV) or to file a claim or objection while you were there? (enter number)')
    M = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Was anyone prevented from scrutinizing the Preliminary Register of Voters (PRV)? (tick Yes or No)')
    N = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Was anyone prevented from filing a Claim to have his/her name added to or corrected on the Preliminary Register of Voters (PRV) (tick Yes or No)')
    P = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Was anyone prevented from filing an Objection to have a name deleted from the Preliminary Register of Voters (PRV) (tick Yes or No)')
    Q = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text="Did anyone attempt to disrupt voters' registration at the centre? (tick Yes or No)")
    R = models.PositiveSmallIntegerField(blank=True, default=0, choices=YES_NO, help_text='Did anyone attempt to intimidate or harass people in or around the centre? (tick Yes or No)')
    S = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many people have filed Claims according to the Summary of Returns for the Display Period Form EC.5A (enter number)')
    T = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many Objections have been filed according to the Summary of Returns for the Display Period Form EC.5A (enter number)')
    U = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many Death Notices have been filed according to the Summary of Returns for the Display Period Form EC.5A (enter number)')
    V = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many Inclusion have been made according to the Summary of Actions Taken by the Revision Officer - Form EC.6A (enter number)')
    W = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many Corrections have been made according to the Summary of Actions Taken by the Revision Officer - Form EC.6A (enter number)')
    X = models.IntegerField(blank=True, null=True, help_text='So far (total to date), how many Deletions have been made according to the Summary of Actions Taken by the Revision Officer - Form EC.6A (enter number)')
    comment = models.CharField(max_length=200, blank=True)
    submitted = models.BooleanField(default=False, help_text="This field tracks if (even though already created), this report has been submitted by the reporter")
    report_rc = models.CharField(blank=True, null=True, max_length=100, help_text="Registration Center as supplied by the data entry operator")
    report_rcid = models.CharField(blank=True, null=True, max_length=50, help_text="Registration Center ID as supplied by the data entry operator")
    audit_log = AuditLog()

    def __unicode__(self):
        return "DCO Checklist for %s from %s on %s" % (self.location, self.observer, self.date)
    
    class Meta:
        permissions = (
            ('view_dcochecklist', 'Can view dco checklist'),
        )

class DCOIncident(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField(db_index=True)
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
    comment = models.CharField(max_length=200, blank=True)
    audit_log = AuditLog()

    def __unicode__(self):
        return "DCO Incident for %s from %s on %s" % (self.location, self.observer, self.date)
    
    class Meta:
        permissions = (
            ('view_dcoincident', 'Can view dco incident'),
        )
        
class EDAYChecklist(models.Model):
    '''The flags defined in this model compute conflicts for different sections of this checklist model and set 
    a true when there is an agreement and a false when there is a conflict'''
    
    VA_OPENTIME = ((1, 'Open by 8AM (1)'), (2, 'Between 8AM & 9AM (2)'), (3, 'Between 9AM & 12 noon (3)'), (4, 'After by 12 noon (4)'), (5, 'Never Started (5)'))
    VP_OPENTIME = ((1, 'Before 1PM (1)'), (2, 'Between 1PM & 2PM (2)'), (3, 'Between 2PM & 3PM (3)'), (4, 'After 3PM (4)'), (5, 'Never Started (5)'))
    TURNOVER = ((1, 'No one'), (2, 'A Few'), (3, 'Half'), (4, 'Most'), (5, 'Everyone'))
    YES_NO = ((0, 'Unspecified'), (1, 'Yes'), (2, 'No'), (3, "Don't Know"))
    EDAY_CHECK = (('1', '1stObserver'), ('2', '2ndObserver'), ('3', 'Control'))
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateField(db_index=True)
    AA = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Had any polling officials arrived by 7:30AM?')
    BA = models.IntegerField(blank=True, null=True, choices=VA_OPENTIME, help_text='What time did the accreditation begin? (tick one)')
    BB = models.IntegerField(blank=True, null=True, help_text="What is the unit's three digit INEC code? (this is public information)")
    BC = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Was the polling station divided into two or more sub-units? (tick one)')
    BD = models.IntegerField(blank=True, null=True, help_text='How many polling officials were present? (enter number)')
    BE = models.IntegerField(blank=True, null=True, help_text='How many political party agents were present? (enter number)')
    BF = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Were any security personnel present? (tick one)')
    BG = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was anyone accredited to vote who did not have a voter\'s card? (tick one)')
    BH = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Did polling officials make a tick to the left of every accredited voters name in the register of voters? (tick one)')
    BJ = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Did the polling officials mark the cuticle on a left finger of every accredited voter? (tick one)')
    BK = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Was everyone who arrived before accreditation of voters finished allowed to be accredited? (tick one)')
    BM = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='How many people left the polling unit after being accredited to vote?(Accredited voters should remain at the polling unit until voting) (tick one)')
    BN = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Did anyone attempt to harass/intimidate voters/polling officials during accreditation? (tick one)')
    BP = models.IntegerField(blank=True, null=True, help_text='How many people were accredited to vote (as announced by the INEC official)? (enter number)')
    CA = models.IntegerField(blank=True, null=True, choices=VP_OPENTIME, help_text='What time did the voting begin? (tick one)')
    CB = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Was the ballot box shown to be empty before being closed and locked? (tick one)')
    CC = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was anyone permitted to vote who did not have a voter\'s card and indelible ink on the cuticle of a left finger? (Every voter should have both)(tick one)')
    CD = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Did polling officials check for every voters name in the register of voters? (tick one)')
    CE = models.IntegerField(blank=True, null=True, choices=TURNOVER, help_text='Was every ballot paper stamped and signed before being given to voters? (tick one)')
    CF = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Were voters able to mark their ballot paper in secret? (tick one)')
    CG = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Was anyone accredited to vote after the accreditation of voters process was closed? (tick one)')
    CH = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Did anyone attempt to harass/intimidate voters/polling officials during the voting process? (tick one)')
    CJ = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Were the ballot papers properly sorted according to each political party? (tick one)')
    CK = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Were the results announced? (tick one)')
    CM = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Did any political party agent disagree with the announced results? (tick one)')
    CN = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Were the results posted in a public place easy for people to see? (tick one)')
    CP = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Did you agree with the official results? (tick one)')
    CQ = models.PositiveSmallIntegerField(blank=True, null=True, default=0, choices=YES_NO, help_text='Did anyone attempt to harass/intimidate polling officials during counting? (tick one)')
    DA = models.IntegerField(blank=True, null=True, help_text='Number of voters on the Register')
    DB = models.IntegerField(blank=True, null=True, help_text='Number of Ballot Papers issued to the Polling Unit')
    DC = models.IntegerField(blank=True, null=True, help_text='Number of Accredited Voters')
    DD = models.IntegerField(blank=True, null=True, help_text='Number of Unused Ballot Papers')
    DE = models.IntegerField(blank=True, null=True, help_text='Number of Spoilt Ballot Papers')
    DF = models.IntegerField(blank=True, null=True, help_text='Number of Rejected Ballots')
    DG = models.IntegerField(blank=True, null=True, help_text='Number of Total Valid Votes')
    DH = models.IntegerField(blank=True, null=True, help_text='Total Number of Used Ballot Papers')
    EA = models.IntegerField(blank=True, null=True)
    EB = models.IntegerField(blank=True, null=True)
    EC = models.IntegerField(blank=True, null=True)
    ED = models.IntegerField(blank=True, null=True)
    EE = models.IntegerField(blank=True, null=True)
    EF = models.IntegerField(blank=True, null=True)
    EG = models.IntegerField(blank=True, null=True)
    EH = models.IntegerField(blank=True, null=True)
    EJ = models.IntegerField(blank=True, null=True)
    EK = models.IntegerField(blank=True, null=True)
    EM = models.IntegerField(blank=True, null=True)
    EN = models.IntegerField(blank=True, null=True)
    EP = models.IntegerField(blank=True, null=True)
    EQ = models.IntegerField(blank=True, null=True)
    ER = models.IntegerField(blank=True, null=True)
    ES = models.IntegerField(blank=True, null=True)
    ET = models.IntegerField(blank=True, null=True)
    EU = models.IntegerField(blank=True, null=True)
    EV = models.IntegerField(blank=True, null=True)
    EW = models.IntegerField(blank=True, null=True)
    EX = models.IntegerField(blank=True, null=True)
    EY = models.IntegerField(blank=True, null=True)
    EZ = models.IntegerField(blank=True, null=True)
    FA = models.IntegerField(blank=True, null=True)
    FB = models.IntegerField(blank=True, null=True)
    FC = models.IntegerField(blank=True, null=True)
    FD = models.IntegerField(blank=True, null=True)
    FE = models.IntegerField(blank=True, null=True)
    FF = models.IntegerField(blank=True, null=True)
    FG = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True, auto_now=True)
    
    comment = models.CharField(max_length=200, blank=True)
    submitted = models.BooleanField(default=False, help_text="This field tracks if (even though already created), this report has been submitted by the reporter")
    checklist_index = models.CharField(max_length=1, default='1', choices=EDAY_CHECK, help_text='This fields helps to identify the reporter sending a particular checklist', db_index=True)
    sms_status_5th = models.PositiveIntegerField(default=3, blank=True, help_text="Field to track the completion status of the fifth SMS")
    audit_log = AuditLog()
    
    @property
    @cache
    def other(self):
        if self.checklist_index in [eday[0] for eday in EDAYChecklist.EDAY_CHECK[:2]]:
            other_index = EDAYChecklist.EDAY_CHECK[0][0] if self.checklist_index == EDAYChecklist.EDAY_CHECK[1][0] else EDAYChecklist.EDAY_CHECK[1][0]
            try:
                return EDAYChecklist.objects.select_related().get(date=self.date, observer=self.observer.twin, checklist_index=other_index)
            except EDAYChecklist.DoesNotExist:
                return None
        else:
            return None
    
    @property
    @cache
    def control(self):
        if self.checklist_index == EDAYChecklist.EDAY_CHECK[2]:
            return None
        else:
            try:
                return EDAYChecklist.objects.select_related().get(date=self.date, observer=self.observer if self.observer.position==1 else self.observer.twin, checklist_index=EDAYChecklist.EDAY_CHECK[2][0], location_type=self.location_type, location_id=self.location_id)
            except EDAYChecklist.DoesNotExist:
                return None
    
    @property
    @cache
    def contesting(self):
        try:
            if self.date == datetime.date(datetime(2011, 4, 26)): # date of guber elections
                return self.observer.state.contesting_set.values_list('code', flat=True)
            else:
                # the presidential elections parties are stored with no state in particular
                return Contesting.objects.filter(state=None).values_list('code', flat=True)
        except AttributeError:
            return []
        
    @property
    @cache
    def parties(self):
        if self.date == datetime.date(datetime(2011, 4, 26)): # date of guber elections
            return dict(self.observer.state.contesting_set.values_list('code','party__code'))
        else:
            # the presidential elections parties are stored with no state in particular
            return dict(Contesting.objects.filter(state=None).values_list('code', 'party__code'))
            
    @property
    @cache
    def flag1(self):
        '''Returns a true when there is an aggreement'''
        if not self.checklist_index == 3 and ((self.AA == self.other.AA) or not self.other.AA or not self.AA):
            return True
        return False
    
    @property
    @cache
    def control_flag1(self):
        '''Returns a true if there is a defined value for the control checklist in this group'''
        if not self.checklist_index == 3 and self.control.AA:
            return True
        return False
    
    @property
    @cache
    def flag2(self):
        if not self.checklist_index == 3 and (self.BA == self.other.BA or not self.other.BA or not self.BA) \
            and (self.BB == self.other.BB or not self.other.BB or not self.BB) \
            and (self.BC == self.other.BC or not self.other.BC or not self.BC) \
            and (self.BD == self.other.BD or not self.other.BD or not self.BD) \
            and (self.BE == self.other.BE or not self.other.BE or not self.BE) \
            and (self.BF == self.other.BF or not self.other.BF or not self.BF) \
            and (self.BG == self.other.BG or not self.other.BG or not self.BG) \
            and (self.BH == self.other.BH or not self.other.BH or not self.BH) \
            and (self.BJ == self.other.BJ or not self.other.BJ or not self.BJ) \
            and (self.BK == self.other.BK or not self.other.BK or not self.BK) \
            and (self.BM == self.other.BM or not self.other.BM or not self.BM) \
            and (self.BN == self.other.BN or not self.other.BN or not self.BN) \
            and (self.BP == self.other.BP or not self.other.BP or not self.BP):
            return True
        return False

    @property
    @cache
    def control_flag2(self):
        if not self.checklist_index == 3 and (self.BA == self.other.BA or self.control.BA) \
            and (self.BB == self.other.BB or self.control.BB) \
            and (self.BC == self.other.BC or self.control.BC) \
            and (self.BD == self.other.BD or self.control.BD) \
            and (self.BE == self.other.BE or self.control.BE) \
            and (self.BF == self.other.BF or self.control.BF) \
            and (self.BG == self.other.BG or self.control.BG) \
            and (self.BH == self.other.BH or self.control.BH) \
            and (self.BJ == self.other.BJ or self.control.BJ) \
            and (self.BK == self.other.BK or self.control.BK) \
            and (self.BM == self.other.BM or self.control.BM) \
            and (self.BN == self.other.BN or self.control.BN) \
            and (self.BP == self.other.BP or self.control.BP):
            return True
        return False
        
    @property
    @cache
    def flag3(self):
        if not self.checklist_index == 3 and (self.CA == self.other.CA or not self.other.CA or not self.CA) \
            and (self.CB == self.other.CB or not self.other.CB or not self.CB) \
            and (self.CC == self.other.CC or not self.other.CC or not self.CC) \
            and (self.CD == self.other.CD or not self.other.CD or not self.CD) \
            and (self.CE == self.other.CE or not self.other.CE or not self.CE) \
            and (self.CF == self.other.CF or not self.other.CF or not self.CF) \
            and (self.CG == self.other.CG or not self.other.CG or not self.CG) \
            and (self.CH == self.other.CH or not self.other.CH or not self.CH) \
            and (self.CJ == self.other.CJ or not self.other.CJ or not self.CJ) \
            and (self.CK == self.other.CK or not self.other.CK or not self.CK) \
            and (self.CM == self.other.CM or not self.other.CM or not self.CM) \
            and (self.CN == self.other.CN or not self.other.CN or not self.CN) \
            and (self.CP == self.other.CP or not self.other.CP or not self.CP) \
            and (self.CP == self.other.CQ or not self.other.CQ or not self.CQ):
            return True
        return False
    
    @property
    @cache
    def control_flag3(self):
        if not self.checklist_index == 3 and (self.CA == self.other.CA or self.control.CA) \
            and (self.CB == self.other.CB or self.control.CB) \
            and (self.CC == self.other.CC or self.control.CC) \
            and (self.CD == self.other.CD or self.control.CD) \
            and (self.CE == self.other.CE or self.control.CE) \
            and (self.CF == self.other.CF or self.control.CF) \
            and (self.CG == self.other.CG or self.control.CG) \
            and (self.CH == self.other.CH or self.control.CH) \
            and (self.CJ == self.other.CJ or self.control.CJ) \
            and (self.CK == self.other.CK or self.control.CK) \
            and (self.CM == self.other.CM or self.control.CM) \
            and (self.CN == self.other.CN or self.control.CN) \
            and (self.CP == self.other.CP or self.control.CP) \
            and (self.CP == self.other.CQ or self.control.CQ):
            return True
        return False

    @property
    @cache
    def flag4(self):
        if not self.checklist_index == 3 and (self.DA == self.other.DA or not self.other.DA or not self.DA) \
            and (self.DB == self.other.DB or not self.other.DB or not self.DB) \
            and (self.DC == self.other.DC or not self.other.DC or not self.DC) \
            and (self.DD == self.other.DD or not self.other.DD or not self.DD) \
            and (self.DE == self.other.DE or not self.other.DE or not self.DE) \
            and (self.DF == self.other.DF or not self.other.DF or not self.DF) \
            and (self.DG == self.other.DG or not self.other.DG or not self.DG) \
            and (self.DH == self.other.DH or not self.other.DH or not self.DH):
            return True
        return False

    @property
    @cache
    def control_flag4(self):
        if not self.checklist_index == 3 and (self.DA == self.other.DA or self.control.DA) \
            and (self.DB == self.other.DB or self.control.DB) \
            and (self.DC == self.other.DC or self.control.DC) \
            and (self.DD == self.other.DD or self.control.DD) \
            and (self.DE == self.other.DE or self.control.DE) \
            and (self.DF == self.other.DF or self.control.DF) \
            and (self.DG == self.other.DG or self.control.DG) \
            and (self.DH == self.other.DH or self.control.DH):
            return True
        return False

    @property
    @cache
    def flag5(self):
        if not self.checklist_index == 3:
            contesting_party_codes = self.contesting
            flag = True
        
            for party_code in contesting_party_codes:
                flag = flag and (getattr(self, party_code) == getattr(self.other, party_code) or not getattr(self.other, party_code) or not getattr(self, party_code))
            return flag
        else:
            return False
    
    @property
    @cache
    def control_flag5(self):
        if not self.checklist_index == 3:
            contesting_party_codes = self.contesting
            flag = True

            for party_code in contesting_party_codes:
                flag = flag and (getattr(self, party_code) == getattr(self.other, party_code) or getattr(self.control, party_code))
            return flag
        else:
            return False

    def __unicode__(self):
        return "EDAY Checklist for %s from %s on %s" % (self.location, self.observer, self.date)
    
    class Meta:
        permissions = (
            ('view_edaychecklist', 'Can view eday checklist'),
        )

class EDAYChecklistOverrides(models.Model):
    """Tracks fields that are overriden in the EDAYChecklist"""
    field = models.CharField(max_length=2)
    checklist = models.ForeignKey(EDAYChecklist, limit_choices_to = {'checklist_index': '3'})

    def __unicode__(self):
        return "%s -> %s" % (self.checklist, self.field)

class EDAYIncident(models.Model):
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    observer = models.ForeignKey(Observer)
    date = models.DateTimeField(db_index=True)
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
    R = models.NullBooleanField(blank=True)
    S = models.NullBooleanField(blank=True)
    T = models.NullBooleanField(blank=True)

    comment = models.CharField(max_length=200, blank=True)
    audit_log = AuditLog()

    def __unicode__(self):
        return "EDAY Incident for %s from %s on %s" % (self.location, self.observer, self.date)

    class Meta:
        permissions = (
            ('view_edayincident', 'Can view eday incident'),
        )

# Make sure the `to` and `null` parameters will be ignored
rules = [((fields.LastUserField,),
    [],
    {
        'to': ['rel.to', {'default': User}],
        'null': ['null', {'default': True}],
    },)]

# Add the rules for the `LastUserField`
add_introspection_rules(rules, ['^audit_log\.models\.fields\.LastUserField'])


class Access(models.Model):
    class Meta:
        permissions = (
            ('can_analyse', 'Can Analyse'),
            ('can_manage_data','Can Manage Data'),
            ('can_administer', 'Can Administer'),
        )

from urllib import quote_plus, urlencode
import urllib2

class Party(models.Model):
    name = models.CharField("Party Full Name",max_length=100, blank="true", null="true")
    code = models.CharField("Political Party", max_length=5, db_index=True)
    
    def __unicode__(self):
        return self.code
    
    class Meta:
        verbose_name_plural = "Parties"
        ordering = ['code']
                
class Contesting(models.Model):
    code = models.CharField("Checklist Code", max_length=2)
    party = models.ForeignKey(Party)
    state = models.ForeignKey(State, blank=True, null=True)
    
    def __unicode__(self):
        return '%s State %s has the code: %s' % (self.state.name, self.party.code, self.code)
    
    class Meta:
        verbose_name_plural = "Contesting"

class NodSMS():
    endpoint_sendsms = 'http://api.nodsms.com/index.php'
    endpoint_balance = 'http://api.nodsms.com/credit.php?user=%(user)s&pass=%(pass)s'
    user = settings.SMS_USER
    pwd  = settings.SMS_PASS

    def sendsms(self, to, msg, sender="SwiftCount"):
        result = urllib2.urlopen(self.endpoint_sendsms, urlencode({
            'user': self.user,
            'pass': self.pwd,
            'from': sender,
            'to': to,
            'msg': msg})).read()
        if result.strip() == 'sent':
            return True
        else:
            return False

    def credit_balance(self):
        try:
            result = urllib2.urlopen(self.endpoint_balance % {'user': quote_plus(self.user), 'pass': quote_plus(self.pwd) }).read()
            if result.isdigit():
                return int(result)
            else:
                return 0
        except urllib2.URLError:
            return 0

# signals
def edaychecklist_handler(sender, **kwargs):
    # don't process 'control' checklists
    if not kwargs['instance'].checklist_index == '3' and not kwargs['created']:
        other_checklist = kwargs['instance'].other
        control_checklist = kwargs['instance'].control
        # only fetch fields that have not been overridden in the control checklist
        available_fields = filter(lambda field: field not in EDAYChecklistOverrides.objects.filter(checklist=control_checklist).values_list('field', flat=True), map(lambda field: field.attname, kwargs['instance']._meta.fields[5:-5]))
        
        for field in available_fields:
            # we'll only propagate values from a checklist to the control if the value for the current checklist matches
            # that of the other checklist or the current checklist has a value and the other doesn't
            try:
                if getattr(kwargs['instance'], field) and ((getattr(kwargs['instance'], field) == getattr(other_checklist, field)) or not getattr(other_checklist, field)):
                    setattr(control_checklist, field, getattr(kwargs['instance'], field))
                
                # if the above didn't execute, we want to be sure there's no conflict, if there is
                # we must make sure the control checklist's value gets blanked
                elif getattr(kwargs['instance'], field) and getattr(other_checklist, field):
                    setattr(control_checklist, field, None)
                
                # if field values for both checklists are the same, freeze the override
                # essentially it locks the control checklist field so data doesn't get overriden by 
                # incoming data
                #if getattr(kwargs['instance'], field) and (getattr(kwargs['instance'], field) == getattr(other_checklist, field)):
                #    obj, created = EDAYChecklistOverrides.objects.get_or_create(field=field, control_checklist)
            except AttributeError:
                pass
        try:
            control_checklist.save()
        except AttributeError:
            pass

# while creating checklists, this signal will need to be disabled
post_save.connect(edaychecklist_handler, sender=EDAYChecklist)

def edaychecklist_5th_sms_handler(sender, **kwargs):
    '''This method computes the status for the 5th SMS:
    1 - Complete
    2 - Partially completed
    3 - None submitted'''
    if not kwargs['instance'].checklist_index == '3' and kwargs['instance'].contesting:
        # compute 5th sms completion status
        contesting_party_codes = kwargs['instance'].contesting
        and_condition = True
        or_condition = False
        for party_code in contesting_party_codes:
            and_condition = and_condition and getattr(kwargs['instance'], party_code)
            or_condition = or_condition or getattr(kwargs['instance'], party_code)

        if and_condition:
            kwargs['instance'].sms_status_5th = 1
        elif or_condition:
            kwargs['instance'].sms_status_5th = 2
        else:
            kwargs['instance'].sms_status_5th = 3

pre_save.connect(edaychecklist_5th_sms_handler, sender=EDAYChecklist)

def observer_location_handler(sender, **kwargs):
    '''This method computes the various location parameters for observers:
    Zone, State, District, LGA and Polling Station/Registration Center'''
    # compute zone
    if kwargs['instance'].role in ['ZC']:
        kwargs['instance'].zone = kwargs['instance'].location
    if kwargs['instance'].role in ['SC', 'NS', 'NSC']:
        kwargs['instance'].zone = kwargs['instance'].location.parent
    elif kwargs['instance'].role == 'SDC':
        kwargs['instance'].zone = kwargs['instance'].location.parent.parent
    elif kwargs['instance'].role == 'LGA':
        kwargs['instance'].zone = kwargs['instance'].location.parent.parent.parent
    elif kwargs['instance'].role == 'OBS':
        kwargs['instance'].zone = kwargs['instance'].location.parent.parent.parent.parent
    
    # compute state
    if kwargs['instance'].role in ['SC', 'NS', 'NSC']:
        kwargs['instance'].state = kwargs['instance'].location
    elif kwargs['instance'].role == 'SDC':
        kwargs['instance'].state = kwargs['instance'].location.parent
    elif kwargs['instance'].role == 'LGA':
        kwargs['instance'].state = kwargs['instance'].location.parent.parent
    elif kwargs['instance'].role == 'OBS':
        kwargs['instance'].state = kwargs['instance'].location.parent.parent.parent
    else:
        kwargs['instance'].state = None

    # compute district
    if kwargs['instance'].role == 'SDC':
        kwargs['instance'].district = kwargs['instance'].location
    if kwargs['instance'].role == 'LGA':
        kwargs['instance'].district = kwargs['instance'].location.parent
    elif kwargs['instance'].role == 'OBS':
        kwargs['instance'].district = kwargs['instance'].location.parent.parent
    else:
        kwargs['instance'].district = None

    # compute lga
    if kwargs['instance'].role == 'LGA':
        kwargs['instance'].lga = kwargs['instance'].location
    elif kwargs['instance'].role == 'OBS':
        kwargs['instance'].lga = kwargs['instance'].location.parent
    else:
        kwargs['instance'].lga = None
        
    # compute ps
    if kwargs['instance'].role == 'OBS':
        kwargs['instance'].ps = kwargs['instance'].location
    else:
        kwargs['instance'].ps = None

pre_save.connect(observer_location_handler, sender=Observer)
