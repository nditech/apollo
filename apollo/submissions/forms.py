# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import (
    BooleanField, IntegerField, SelectField, SelectMultipleField,
    validators, widgets
)


def generate_submission_form(form, data=None):
    fields = {'groups': []}

    for group in form.groups:
        groupspec = group.name, []

        for field in group.fields:
            # if the field has options, create a list of choices
            if field.options:
                choices = [(k, v) for k, v in field.options.iteriterms()]

                if field.allows_multiple_values:
                    fields[field.name] = SelectMultipleField(
                        choices=choices,
                        description=field.description,
                        option_widget=widgets.CheckboxInput(),
                        widget=widgets.ListWidget(prefix_label=False)
                    )
                else:
                    fields[field.name] = SelectField(
                        choices=choices,
                        description=field.description,
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST':
                    fields[field.name] = IntegerField(
                        description=field.description,
                        validators=[validators.NumberRange(
                            min=field.min_value, max=field.max_value)]
                    )
                else:
                    fields[field.name] = BooleanField(
                        description=field.description
                    )

        fields['groups'].append(groupspec)

    form_class = type('SubmissionForm', (Form,), fields)

    return form_class(data)
