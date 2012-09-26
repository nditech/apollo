from django import forms

from .models import *


def generate_custom_form(form_id):
    # get the form, but allow any exceptions "bubble up"
    form = Form.objects.get(pk=form_id)

    fields = {}

    for group in form.groups.all():
        for field in group.fields.all():
            # are there any field options?
            options = field.options.all()

            if options == []:
                fields[field.tag] = forms.IntegerField(help_text=field.description,
                    max_value=9999, min_value=0)
            else:
                choices = [(option.option, option.description) for option in options]
                fields[field.tag] = forms.ChoiceField(choices=choices,
                    help_text=field.description)

    return type('CustomForm', (forms.BaseForm,), {'base_fields': fields})
