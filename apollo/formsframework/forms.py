# -*- coding: utf-8 -*-
from wtforms import (
    Form, BooleanField, IntegerField, SelectField, SelectMultipleField,
    validators, widgets
)


class BaseQuestionnaireForm(Form):
    def save():
        pass


def build_questionnaire(form, data=None):
    fields = {'groups': []}

    for group in form.groups:
        groupspec = (group.name, [])

        for field in group.fields:
            # if the field has options, create a list of choices
            if field.options:
                choices = [(k, v) for k, v in field.options.iteriterms()]

                if field.allows_multiple_values:
                    fields[field.name] = SelectMultipleField(
                        field.name,
                        choices=choices,
                        description=field.description,
                        option_widget=widgets.CheckboxInput(),
                        widget=widgets.ListWidget(prefix_label=False)
                    )
                else:
                    fields[field.name] = SelectField(
                        field.name,
                        choices=choices,
                        description=field.description,
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST':
                    fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[validators.NumberRange(
                            min=field.min_value, max=field.max_value)]
                    )
                else:
                    fields[field.name] = BooleanField(
                        field.name,
                        description=field.description
                    )

        fields['groups'].append(groupspec)

    form_class = type('QuestionnaireForm', (BaseQuestionnaireForm,), fields)

    return form_class(data)
