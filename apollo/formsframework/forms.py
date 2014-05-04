# -*- coding: utf-8 -*-
from datetime import datetime
from wtforms import (
    Form,
    IntegerField, SelectField, SelectMultipleField, StringField,
    validators, widgets
)
from flask import g
from .. import services, models


class BaseQuestionnaireForm(Form):
    form = StringField(
        u'Form', validators=[validators.required()],
        filters=[lambda data: services.forms.get(pk=data)])
    participant = StringField(
        u'Participant', validators=[validators.required()],
        filters=[lambda data: services.participants.get(participant_id=data)])
    sender = StringField(u'Sender', validators=[validators.required()])
    comment = StringField(u'Comment', validators=[validators.optional()])

    def process(self, formdata=None, obj=None, **kwargs):
        self._formdata = formdata
        return super(BaseQuestionnaireForm, self).process(
            formdata, obj, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(BaseQuestionnaireForm, self).validate(*args, **kwargs)
        if success and self._formdata:
            unknown_fields = filter(
                lambda f: f not in self._fields.keys(),
                self._formdata.keys())
            if unknown_fields:
                if type(self._errors) == dict:
                    self._errors.update({'__all__': unknown_fields})
                else:
                    self._errors = {'__all__': unknown_fields}

                success = False

        return success

    def save(self):
        ignored_fields = ['form', 'participant', 'sender', 'comment']
        try:
            if self.data.get('form').form_type == 'CHECKLIST':
                submission = services.submissions.get(
                    contributor=self.data.get('participant'),
                    form=self.data.get('form'), submission_type='O')
                if self.data.get('comment'):
                    services.submission_comments.create_comment(
                        submission, self.data.get('comment'))
            else:
                submission = models.Submission(
                    form=self.data.get('form'),
                    contributor=self.data.get('participant'),
                    location=self.data.get('participant').location,
                    created=datetime.utcnow(), deployment=g.event.deployment,
                    event=g.event)
                if self.data.get('comment'):
                    submission.description = self.data.get('comment')

            form_fields = filter(lambda f: f not in ignored_fields,
                                 self.data.keys())
            change_detected = False
            for form_field in form_fields:
                if self.data.get(form_field):
                    change_detected = True
                    setattr(submission, form_field, self.data.get(form_field))

            if change_detected:
                submission.save()
        except models.Submission.DoesNotExist:
            pass


def build_questionnaire(form, data=None):
    fields = {'groups': []}

    for group in form.groups:
        groupspec = (group.name, [])

        for field in group.fields:
            # if the field has options, create a list of choices
            if field.options:
                choices = [(v, k) for k, v in field.options.iteritems()]

                if field.allows_multiple_values:
                    fields[field.name] = SelectMultipleField(
                        field.name,
                        choices=choices,
                        coerce=int,
                        description=field.description,
                        option_widget=widgets.CheckboxInput(),
                        validators=[validators.optional()],
                        widget=widgets.ListWidget(prefix_label=False)
                    )
                else:
                    fields[field.name] = SelectField(
                        field.name,
                        choices=choices,
                        coerce=int,
                        description=field.description,
                        validators=[validators.optional()],
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST':
                    fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[
                            validators.optional(),
                            validators.NumberRange(min=field.min_value,
                                                   max=field.max_value)]
                    )
                else:
                    fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[validators.optional()]
                    )

        fields['groups'].append(groupspec)

    form_class = type('QuestionnaireForm', (BaseQuestionnaireForm,), fields)

    return form_class(data)
