from django import forms
from form_utils.forms import BetterForm
from .models import *


# please see https://bitbucket.org/carljm/django-form-utils/overview for
# info on using inside a Django template
def generate_submission_form(form_id):
    # get the form, but allow any exceptions "bubble up"
    form = Form.objects.get(pk=form_id)

    fields = {}  # necessary for the individual fields
    groups = []  # necessary for the internal Meta class definition

    for group in form.groups.all():
        groupspec = (group.name, {'fields': [], 'legend': group.name})
        for field in group.fields.all():
            # are there any field options?
            groupspec[1]['fields'].append(field.tag)
            options = list(field.options.all())

            if options == []:
                upper_limit = field.upper_limit if field.upper_limit != None else 9999
                lower_limit = field.lower_limit if field.lower_limit != None else 0
                fields[field.tag] = forms.IntegerField(help_text=field.description,
                    max_value=upper_limit, min_value=lower_limit)
            else:
                choices = [(option.option, option.description) for option in options]
                fields[field.tag] = forms.ChoiceField(choices=choices,
                    help_text=field.description)

        groups.append(groupspec)

    metaclass = type('Meta', (), {'fieldsets': groups})
    fields['Meta'] = metaclass

    return type('SubmissionForm', (BetterForm,), fields)
