from django.db import models
from django.dispatch import receiver
from django_orm.postgresql import hstore
from mptt.models import MPTTModel, TreeForeignKey
from rapidsms.models import Contact, Backend, Connection
from datetime import datetime
from .managers import SubmissionManager
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
    data = hstore.DictionaryField(db_index=True, null=True, blank=True)

    objects = hstore.HStoreManager()

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
        permissions = (
            ("view_observer", "Can view observers"),
        )

    def __unicode__(self):
        return getattr(self, 'observer_id', "")


class ObserverDataManager(models.Model):
    '''Storage for observer data. Should be a singleton'''
    pass


class ObserverDataField(models.Model):
    data_manager = models.ForeignKey(ObserverDataManager, related_name='fields')
    name = models.CharField(max_length=32) # will allow name to double as key
    description = models.CharField(max_length=255)


class Form(models.Model):
    '''
    Defines the schema for forms that will be managed
    by the application. Of important note are the
    `trigger` and `field_pattern` fields.

    `trigger` stores a regular expression that matches
    the entire text message string (after preliminary
    sanitization) and must contain a "fields" group
    match. This enables the parser to locate the
    section that handles fields parsing. Optionally,
    the `trigger` may contain a "observer" group that
    specifies the string pattern used in searching for
    the observer.

    It's most likely that the pattern for the "fields"
    group will match with that of `field_pattern`. This
    parameter is used to locate other fields that may
    parse correctly in the general form matching phase
    but not be a valid field in the individual field
    parsing phase.

    `field_pattern` must be defined to include groups with
    the names: "key" representing the field tag and "value"
    representing the expected value.
    '''
    name = models.CharField(max_length=255)
    trigger = models.CharField(max_length=255, unique=True)
    field_pattern = models.CharField(max_length=255)
    autocreate_submission = models.BooleanField(default=False,
        help_text="Whether to create a new record if a submission doesn't exist")

    def __unicode__(self):
        return self.name

    def match(self, text):
        if re.match(self.trigger, text, flags=re.I):
            return True

    @staticmethod
    def parse(text):
        forms = Form.objects.all()
        submission = {'data': {}}
        observer = None

        # iterate over all forms, until we get a match
        for form in forms:
            if form.match(text):
                match = re.match(form.trigger, text, flags=re.I)
                fields_text = match.group('fields')

                if 'observer' in match.groupdict().keys():
                    try:
                        observer = Observer.objects.get(observer_id=match.group('observer'))
                    except Observer.DoesNotExist:
                        pass

                # begin submission processing
                submission['form'] = form
                submission['range_error_fields'] = []
                submission['attribute_error_fields'] = []

                '''
                In each loop, each field is expected to parse
                their own values out and remove their tags from
                the field text. If any text is left after parsing
                every field, then we're likely to have a field
                attribute error
                '''
                for group in form.groups.all():
                    for field in group.fields.all():
                        fields_text = field.parse(fields_text)
                        if field.value == -1:
                            submission['range_error_fields'].append(field.tag)
                        elif field.value:
                            submission['data'][field.tag.upper()] = str(field.value)
                if fields_text:
                    for field in re.finditer(form.field_pattern, fields_text, flags=re.I):
                        submission['attribute_error_fields'].append(field.group('key'))
                break
        else:
            raise Form.DoesNotExist
        return (submission, observer)


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
    upper_limit = models.IntegerField(null=True, default=9999)
    lower_limit = models.IntegerField(null=True, default=0)
    present_true = models.BooleanField(default=False)
    value = None

    class Meta:
        order_with_respect_to = 'group'

    def __unicode__(self):
        return '%s -> %s' % (self.group, self.tag,)

    def parse(self, text):
        pattern = r'{0}(?P<value>\d*)'.format(self.tag)

        match = re.search(pattern, text, re.I)

        if match:
            field_value = int(match.group('value')) \
                if match.group('value') else None

            if field_value:
                if self.options.all().count():
                    for option in self.options.all():
                        if option.option == field_value:
                            self.value = field_value
                            break
                    else:
                        self.value = -1
                else:
                    if field_value < self.lower_limit or field_value > self.upper_limit:
                        self.value = -1
                    else:
                        self.value = field_value
            elif self.present_true:
                # a value of 1 indicates presence/truth
                self.value = 1

        return re.sub(pattern, '', text, flags=re.I) if self.value else text


class FormFieldOption(models.Model):
    field = models.ForeignKey(FormField, related_name="options")
    description = models.CharField(max_length=255)
    option = models.PositiveIntegerField()

    class Meta:
        order_with_respect_to = 'field'

    def __unicode__(self):
        return '%s -> %s' % (self.field, self.option,)


class Submission(models.Model):
    form = models.ForeignKey(Form, related_name='submissions')
    observer = models.ForeignKey(Observer, blank=True, null=True)
    location = models.ForeignKey(Location, related_name="submissions")
    date = models.DateField(default=datetime.today())
    data = hstore.DictionaryField(db_index=True, null=True, blank=True)
    overrides = hstore.DictionaryField(db_index=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SubmissionManager()

    def __unicode__(self):
        return u"%s -> %s" % (self.pk, self.observer,)

    class Meta:
        permissions = (
            ("view_submission", "Can view submissions"),
        )

    def siblings(self):
        return Submission.objects.exclude(pk=self.pk).exclude(observer=None).filter(location=self.location)

    def master(self):
        # should only return one object for this method
        try:
            return Submission.objects.exclude(pk=self.pk).get(location=self.location, observer=None)
        except Submission.DoesNotExist:
            return None

    def _get_completion(self, group):
        if not group in self.form.groups.all():
            return None

        tags = [field.tag for field in group.fields.all()]

        truthy = [tag in self.data for tag in tags]

        return truthy

    def is_complete(self, group):
        truthy = self._get_completion(group)

        if truthy is None:
            return None

        return all(truthy)

    def is_partial(self, group):
        truthy = self._get_completion(group)

        if truthy is None:
            return None

        return any(truthy)

    def is_missing(self, group):
        truthy = self._get_completion(group)

        if truthy is None:
            return None

        return not any(truthy)

@receiver(models.signals.post_save, sender=Observer, dispatch_uid='create_contact')
def create_contact(sender, **kwargs):
    if kwargs['created']:
        contact = Contact()
        contact.observer = kwargs['instance']
        contact.save()


@receiver(models.signals.post_delete, sender=Observer, dispatch_uid='delete_contact')
def delete_contact(sender, **kwargs):
    kwargs['instance'].contact.delete()

# the below function generates a comparison function
def make_value_check(a):
    def value_check(b):
        if a is None and b is not None:
            return 0
        if a is not None and b is None:
            return 0 # either but not both values exist
        if a == b:
            return 1 # values match
        return -1 # value exists but doesn't match


    return value_check


@receiver(models.signals.post_save, sender=Submission, dispatch_uid='sync_checklists')
def sync_checklists(sender, **kwargs):
    # grab sibling and master checklists
    instance = kwargs['instance']

    # quit if this is the master
    if instance.observer is None:
        return

    siblings = list(instance.siblings())
    master = instance.master()

    # if no siblings exist, copy to master and quit
    if not siblings:
        for key in instance.data.keys():
            if key in master.overrides:
                continue
            master.data[key] = instance.data[key]

        master.save()

    # get all possible keys
    key_set = set(instance.data.keys())
    for sibling in siblings:
        key_set.update(sibling.data.keys)

    # this be pure hackery
    for key in key_set:
        # if the key has already been overridden, don't do anything
        if key in master.overrides:
            continue

        # get the value set for this key, and create a comparison function
        # for that value (see make_value_check definition).
        current = instance.data.get(key, None)
        checker_function = make_value_check(current)

        # the map() call executes the inner value_check function with a = current
        # and b = each item from the list comprehension
        checked_values = map(checker_function, [sibling.data.get(key, None) for sibling in siblings])

        if -1 in checked_values:
            # only if the key is set to different values across all siblings
            master.data.pop(key, None)
            continue

        if master.data.get(key, None) is None and current is not None:
            # if the key has not been set on the master and this instance
            # has it set
            master.data[key] = current

    master.save()
