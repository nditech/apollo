from django import forms
from django.utils.encoding import force_unicode
from form_utils.forms import BetterForm
from apollo.core.models import (Form, Observer, ObserverDataField, Location, Submission, Activity)
from rapidsms.models import (Backend, Contact, Connection)


# custom hidden input widget for locations
class LocationHiddenInput(forms.HiddenInput):
    def render(self, name, value, attrs=None, choices=()):
        if value:
            try:
                obj = self.choices.queryset.get(pk=value)
                selected_choice = self.choices.choice(obj)
                attrs.update({'data-name': force_unicode(selected_choice[1]),
                    'data-type': force_unicode(obj.type.name)})
            except self.choices.queryset.__class__.DoesNotExist:
                pass
        return super(LocationHiddenInput, self).render(name, value, attrs)


class SubmissionModelForm(BetterForm):
    FORM = None  # The form this submission will be saved to
    STATUS_CHOICES = (
        ('', 'Unmarked'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')
    )
    WITNESS_CHOICES = (
        ('', 'Unspecified'),
        ('witnessed', 'I witnessed the incident'),
        ('after', 'I arrived just after the incident'),
        ('reported', 'The incident was reported to me by someone else'),
    )

    location = forms.ModelChoiceField(queryset=Location.objects.all(),
        required=False, widget=LocationHiddenInput(
            attrs={'class': 'span6 select2-locations', 'placeholder': 'Location'}))
    observer = forms.ModelChoiceField(queryset=Observer.objects.all(),
        required=False, widget=forms.HiddenInput(
            attrs={'class': 'span5 select2-observers', 'placeholder': 'Observer'}))
    data__description = forms.CharField(widget=forms.Textarea(attrs={'cols': '40', 'rows': '5', 'style': 'width:40%'}), required=False)
    data__location = forms.CharField(required=False, widget=forms.HiddenInput())
    data__status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)
    data__witness = forms.ChoiceField(required=False, choices=WITNESS_CHOICES)

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            self.instance = kwargs.pop('instance')

            if self.instance:
                kwargs['initial'] = {
                    'location': self.instance.location,
                    'observer': self.instance.observer,
                    'form': self.instance.form
                }
                kwargs['initial'].update(
                    {'data__{}'.format(k): v.split(',') if ',' in v else v for k, v in self.instance.data.items()}
                )

        return super(BetterForm, self).__init__(*args, **kwargs)

    def save(self):
        cleaned_data = self.cleaned_data

        # retrieve submission data fields
        data = {k.replace('data__', ''): v for k, v in cleaned_data.items() if k.startswith('data__')}

        for key in data.keys():
            if data[key] != None and data[key] != False and data[key] != '':
                # the forced casting to integer enables the conversion of boolean values
                # as is the case for incidents that are returned as boolean and need to
                # be converted to integer (and then string) before storage
                if isinstance(data[key], list):
                    data[key] = ','.join(data[key])
                elif not (isinstance(data[key], unicode) or isinstance(data[key], str)):
                    data[key] = str(int(data[key]))
            else:
                del data[key]

        if hasattr(self, 'instance') and self.instance:
            # test for overriden values and indicate
            if self.instance.form.type == 'CHECKLIST':
                for tag in frozenset(data.keys() + self.instance.data.keys()):
                    # the XOR operator is used to check for cases where they are
                    # not the same
                    if ((tag in data) ^ (tag in self.instance.data)) or (data[tag] != self.instance.data[tag]):
                        self.instance.overrides.update({tag: '1'})

            # save updated location information if this is an incident report
            if self.instance.form.type == 'INCIDENT':
                self.instance.location = cleaned_data['location']

            self.instance.data = data

            return self.instance.save()
        else:
            # retrict creation of submissions to only INCIDENTS
            if self.FORM and self.FORM.type == 'INCIDENT' and cleaned_data['observer']:
                # if the location isn't explicitly specified, use that of the observer
                location = cleaned_data['location'] or cleaned_data['observer'].location

                return Submission.objects.create(
                    observer=cleaned_data['observer'],
                    form=self.FORM,
                    location=location,
                    data=data
                    )


class ContactModelForm(forms.ModelForm):
    class Meta:
        model = Observer
        fields = ('observer_id', 'name', 'gender', 'role', 'supervisor',
            'location', 'partner',)

    def __init__(self, *args, **kwargs):
        # sort out 'regular' fields
        super(forms.ModelForm, self).__init__(*args, **kwargs)

        # add phone numbers
        if self.instance.contact:
            phone_set = set([connection.identity for connection in self.instance.contact.connection_set.all()])

            for index, number in enumerate(phone_set):
                label = 'Phone #%d' % (index + 1)
                name = 'conn_%d' % index
                self.fields[name] = forms.CharField(label=label, initial=number)
                kwargs['initial'][name] = number

        # now for the hstore field
        for data_field in ObserverDataField.objects.all():
            key = data_field.name
            value = self.instance.data.get(key, None) if self.instance.data else None
            self.fields[key] = forms.CharField(label=data_field.description,
                initial=value, required=False)

    def save(self):
        clean_data = self.cleaned_data
        data_keys = [field.name for field in ObserverDataField.objects.all()]

        # first off, set data keys
        self.instance.data = {}
        for key in data_keys:
            # remove data key after using it
            value = clean_data.pop(key)
            if value:
                self.instance.data[key] = value

        # set phone numbers
        backends = Backend.objects.all()

        if not self.instance.contact:
            self.instance.contact = Contact.objects.create()

        # clean any attached numbers (no, this doesn't delete any Connection,
        # it just unlinks them from the Contact)
        self.instance.contact.connection_set.clear()

        connection_keys = filter(lambda k: k.startswith('conn'),
            [key for key in clean_data.keys()])

        for key in connection_keys:
            identity = clean_data.pop(key)
            for backend in backends:
                connection, created = Connection.objects.get_or_create(identity=identity,
                    backend=backend)

                self.instance.contact.connection_set.add(connection)

        for key in clean_data:
            setattr(self.instance, key, clean_data[key])

        self.instance.save()

        return self.instance


# please see https://bitbucket.org/carljm/django-form-utils/overview for
# info on using inside a Django template
def generate_submission_form(form, readonly=False):
    fields = {'FORM': form}  # necessary for the individual fields
    groups = []  # necessary for the internal Meta class definition

    for group in form.groups.all():
        groupspec = (group.name, {'fields': [], 'legend': group.name})
        for field in group.fields.all().order_by('tag'):
            field_name = 'data__{}'.format(field.tag)

            # are there any field options?
            groupspec[1]['fields'].append(field_name)
            options = list(field.options.all())

            if options:
                choices = [(option.option, option.description) for option in options]

                if field.allow_multiple:
                    fields[field_name] = forms.MultipleChoiceField(choices=choices,
                        help_text=field.description, required=False, label=field.tag,
                        widget=forms.CheckboxSelectMultiple)
                else:
                    fields[field_name] = forms.ChoiceField(choices=choices,
                        help_text=field.description, required=False, label=field.tag,
                        widget=forms.TextInput(attrs={'class': 'input-mini'}))
            else:
                if form.type == 'CHECKLIST':
                    fields[field_name] = forms.IntegerField(help_text=field.description,
                        max_value=field.upper_limit or 9999, min_value=field.lower_limit or 0,
                        required=False, label=field.tag, widget=forms.TextInput(attrs={'class': 'input-mini'}))
                else:
                    fields[field_name] = forms.BooleanField(help_text=field.description,
                        required=False, label=field.tag, widget=forms.CheckboxInput())

            # Disable the field if the form is readonly
            if readonly:
                fields[field_name].widget.attrs['readonly'] = 'readonly'
                fields[field_name].widget.attrs['disabled'] = 'disabled'

        groups.append(groupspec)

    metaclass = type('Meta', (), {'fieldsets': groups})
    fields['Meta'] = metaclass

    return type('SubmissionForm', (SubmissionModelForm,), fields)


class LocationModelForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('name', 'code', 'type',)

    def save(self):
        clean_data = self.cleaned_data

        for key in clean_data:
            setattr(self.instance, key, clean_data[key])

        self.instance.save()
        return self.instance


class ActivitySelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)
        self.fields['activity'] = forms.ModelChoiceField(
            queryset=Activity.objects.all().order_by('-end_date'),
            initial=request.session.get('activity', Activity.default())
                if request else None,
            empty_label=None,
            widget=forms.Select(attrs={'class': 'input-xlarge'}))
