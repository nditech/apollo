from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from rapidsms.models import Contact
from django.contrib.auth.models import User
from south.modelsinspector import add_introspection_rules
from audit_log.models import fields
from audit_log.models.managers import AuditLog

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

    def __unicode__(self):
        return self.name

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

class Partner(models.Model):
    name = models.CharField("Partner's name", max_length=100)
    code = models.CharField(max_length=10)

    def __unicode__(self):
        return self.code

class Observer(models.Model):
    ROLES = (
        ('NSC', 'National Steering Committee'),
        ('NS', 'National Secretariat'),
        ('ZC', 'Zonal Coordinator'),
        ('SC', 'State Coordinator'),
        ('SDC', 'State Deputy Coordinator'),
        ('LGA', 'LGA Supervisor'),
        ('OBS', 'Observer'))

    contact = models.OneToOneField(Contact, blank=True, null=True)
    dob = models.DateField("Date of Birth", blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=14, null=True, blank=True)
    observer_id = models.CharField(max_length=6)
    location_type = models.ForeignKey(ContentType, null=True, blank=True)
    location_id = models.PositiveIntegerField(null=True, blank=True)
    location = generic.GenericForeignKey("location_type", "location_id")
    supervisor = models.ForeignKey("Observer", related_name="observers", blank=True, null=True)
    partner = models.ForeignKey("Partner", related_name="observers")
    role = models.CharField('Observer Role', max_length=3, choices=ROLES, blank=True)

    def __set_name(self, name):
        self.contact.name = name

    def __get_name(self):
        return self.contact.name

    name = property(__get_name, __set_name)

    def __unicode__(self):
        return self.observer_id

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
    date = models.DateField()
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
    comment = models.CharField(max_length=200, blank=True)
    audit_log = AuditLog()

    def __unicode__(self):
        return "VR Incident for %s from %s on %s" % (self.location, self.observer, self.date)

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
    date = models.DateField()
    sms_serial = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Used in tracking the SMS recieved in a day")
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
    comment = models.CharField(max_length=200, blank=True)
    audit_log = AuditLog()

    def __unicode__(self):
        return "DCO Incident for %s from %s on %s" % (self.location, self.observer, self.date)

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

