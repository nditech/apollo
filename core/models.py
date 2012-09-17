from django.db import models
from django.dispatch import receiver
from django_orm.postgresql import hstore
from mptt.models import MPTTModel, TreeForeignKey
from rapidsms.models import Contact, Backend, Connection
from datetime import datetime
import re


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
    name = models.CharField(max_length=100, null=True, blank=True)
    contact = models.OneToOneField(Contact, related_name='observer', blank=True, null=True)
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location, related_name="observers")
    supervisor = models.ForeignKey('self', null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER, db_index=True)
    partner = models.ForeignKey(Partner, null=True, blank=True)
    data = hstore.DictionaryField(db_index=True, null=True, blank=True)

    objects = hstore.HStoreManager()

    def _get_phone(self):
        return self.contact.connection_set.all()[0].identity \
            if self.contact and self.contact.connection_set.count() else None

    def _set_phone(self, phone):
        for backend in Backend.objects.all():
            try:
                conn = Connection.objects.get(contact=self.contact, backend=backend)
                conn.identity = phone
                conn.save()
            except Connection.DoesNotExist:
                conn = Connection.objects.create(
                    contact=self.contact,
                    backend=backend,
                    identity=phone)

    phone = property(_get_phone, _set_phone)

    class Meta:
        ordering = ['observer_id']

    def __unicode__(self):
        return getattr(self, 'observer_id', "")


class Form(models.Model):
    name = models.CharField(max_length=255)
    trigger = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name

    def match(self, text):
        if re.match(self.trigger, text, re.I):
            return True

    @staticmethod
    def parse(text):
        forms = Form.objects.all()
        submission = {}

        # iterate over all forms, until we get a match
        for form in forms:
            if form.match(text):
                # begin submission processing
                submission['form_id'] = form.pk

                for group in form.groups.all():
                    for field in group.fields.all():
                        text = field.parse(text)
                        submission[field.tag.upper()] = field.value
                break
        else:
            raise Form.DoesNotExist
        return (submission, text)


class FormGroup(models.Model):
    name = models.CharField(max_length=32, blank=True)
    form = models.ForeignKey(Form, related_name='groups')

    class Meta:
        order_with_respect_to = 'form'

    def __unicode__(self):
        return self.name


class FormField(models.Model):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(FormGroup, related_name='fields')
    tag = models.CharField(max_length=8)
    upper_limit = models.IntegerField(null=True)
    lower_limit = models.IntegerField(null=True)
    present_true = models.BooleanField(default=False)
    value = None

    class Meta:
        order_with_respect_to = 'group'

    def __unicode__(self):
        return '%s -> %s' % (self.group, self.tag,)

    def parse(self, text):
        pattern = r'{0}(?P<tagged>\d*)'.format(self.tag)

        match = re.search(pattern, text, re.I)

        if match:
            tagged = match.group('tagged')

            if tagged:
                self.value = int(tagged)
            elif self.present_true:
                # a value of 1 indicates presence/truth
                self.value = 1

        return re.sub(pattern, '', text, re.I) if self.value else text


class Submission(models.Model):
    form = models.ForeignKey(Form, related_name='submissions')
    observer = models.ForeignKey(Observer, blank=True, null=True)
    date = models.DateField(default=datetime.today())
    data = hstore.DictionaryField(db_index=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = hstore.HStoreManager()

    def __unicode__(self):
        return u"%s -> %s" % (self.pk, self.observer,)


@receiver(models.signals.post_save, sender=Observer, dispatch_uid='create_contact')
def create_contact(sender, **kwargs):
    if kwargs['created']:
        contact = Contact()
        contact.observer = kwargs['instance']
        contact.save()


@receiver(models.signals.post_delete, sender=Observer, dispatch_uid='delete_contact')
def delete_contact(sender, **kwargs):
    kwargs['instance'].contact.delete()
