from django import forms
from form_utils.forms import BetterForm
from .models import *


class SubmissionModelForm(BetterForm):
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            self.instance = kwargs['instance']
            del kwargs['instance']
        return super(BetterForm, self).__init__(*args, **kwargs)

    def save(self):
        data = self.cleaned_data
        for key in data.keys():
            if data[key]:
                data[key] = str(data[key])
            else:
                del data[key]

        # test for overriden values and indicate
        for tag in frozenset(data.keys() + self.instance.data.keys()):
            # the XOR operator is used to check for cases where they are
            # not the same
            if ((tag in data) ^ (tag in self.instance.data)) or (data[tag] != self.instance.data[tag]):
                self.instance.overrides.update({tag: '1'})

        self.instance.data = data

        return self.instance.save()


# please see https://bitbucket.org/carljm/django-form-utils/overview for
# info on using inside a Django template
def generate_submission_form(form):
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
                fields[field.tag] = forms.ChoiceField(choices=choices,
                    help_text=field.description, required=False, label=field.tag,
                    widget=forms.TextInput)
            else:
                fields[field.tag] = forms.IntegerField(help_text=field.description,
                    max_value=field.upper_limit or 9999, min_value=field.lower_limit or 0,
                    required=False, label=field.tag)

        groups.append(groupspec)

    metaclass = type('Meta', (), {'fieldsets': groups})
    fields['Meta'] = metaclass

    return type('SubmissionForm', (SubmissionModelForm,), fields)


class ContactForm(forms.ModelForm):
    class Meta:
        model = Observer
        fields = ('observer_id', 'name', 'role', 'location', 'gender',
            'partner',)
