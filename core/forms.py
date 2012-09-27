from django import forms
from form_utils.forms import BetterForm
from .models import *


# please see https://bitbucket.org/carljm/django-form-utils/overview for
# info on using inside a Django template
def generate_custom_form(form_id):
    # get the form, but allow any exceptions "bubble up"
    form = Form.objects.get(pk=form_id)

    fields = {} # necessary for the individual fields
    groups = [] # necessary for the internal Meta class definition

    for group in form.groups.all():
        groupspec = (group.name, {'fields': [], 'legend': group.name})
        for field in group.fields.all():
            # are there any field options?
            groupspec[1]['fields'].append(field.tag)
            options = list(field.options.all())

            if options == []:
                fields[field.tag] = forms.IntegerField(help_text=field.description,
                    max_value=9999, min_value=0)
            else:
                choices = [(option.option, option.description) for option in options]
                fields[field.tag] = forms.ChoiceField(choices=choices,
                    help_text=field.description)

        groups.append(groupspec)

    metaclass = type('Meta', (), {'fieldsets': groups})
    fields['Meta'] = metaclass

    return type('CustomForm', (BetterForm,), fields)
