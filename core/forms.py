from django import forms
from form_utils.forms import BetterForm
from .models import *


class SubmissionModelForm(BetterForm):
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            self.instance = kwargs.pop('instance')

            kwargs['initial'] = self.instance.data

            for key in kwargs['initial'].keys():
                if ',' in kwargs['initial'][key]:
                    kwargs['initial'][key] = kwargs['initial'][key].split(',')

        return super(BetterForm, self).__init__(*args, **kwargs)

    def save(self):
        data = self.cleaned_data
        for key in data.keys():
            if data[key]:
                # the forced casting to integer enables the conversion of boolean values
                # as is the case for incidents that are returned as boolean and need to
                # be converted to integer (and then string) before storage
                if isinstance(data[key], list):
                    data[key] = ','.join(data[key])
                else:
                    data[key] = str(int(data[key]))
            else:
                del data[key]

        # test for overriden values and indicate
        if self.instance.form.type == 'CHECKLIST':
            for tag in frozenset(data.keys() + self.instance.data.keys()):
                # the XOR operator is used to check for cases where they are
                # not the same
                if ((tag in data) ^ (tag in self.instance.data)) or (data[tag] != self.instance.data[tag]):
                    self.instance.overrides.update({tag: '1'})

        self.instance.data = data

        return self.instance.save()


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
    fields = {}  # necessary for the individual fields
    groups = []  # necessary for the internal Meta class definition

    for group in form.groups.all():
        groupspec = (group.name, {'fields': [], 'legend': group.name})
        for field in group.fields.all():
            # are there any field options?
            groupspec[1]['fields'].append(field.tag)
            options = list(field.options.all())

            if options:
                choices = [(option.option, option.description) for option in options]

                if field.allow_multiple:
                    fields[field.tag] = forms.MultipleChoiceField(choices=choices,
                        help_text=field.description, required=False, label=field.tag,
                        widget=forms.CheckboxSelectMultiple)
                else:
                    fields[field.tag] = forms.ChoiceField(choices=choices,
                        help_text=field.description, required=False, label=field.tag,
                        widget=forms.TextInput(attrs={'class': 'input-mini'}))
            else:
                if form.type == 'CHECKLIST':
                    fields[field.tag] = forms.IntegerField(help_text=field.description,
                        max_value=field.upper_limit or 9999, min_value=field.lower_limit or 0,
                        required=False, label=field.tag, widget=forms.TextInput(attrs={'class': 'input-mini'}))
                else:
                    fields[field.tag] = forms.BooleanField(help_text=field.description,
                        required=False, label=field.tag, widget=forms.CheckboxInput())

            # Disable the field if the form is readonly
            if readonly:
                fields[field.tag].widget.attrs['readonly'] = 'readonly'
                fields[field.tag].widget.attrs['disabled'] = 'disabled'

        groups.append(groupspec)

    metaclass = type('Meta', (), {'fieldsets': groups})
    fields['Meta'] = metaclass

    return type('SubmissionForm', (SubmissionModelForm,), fields)
