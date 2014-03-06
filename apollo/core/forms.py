from __future__ import unicode_literals
from django import forms
from django.utils.translation import ugettext_lazy as _
from form_utils.forms import BetterForm
from core.documents import Event, Participant


class BaseQuestionnaireForm(BetterForm):
    prefix = forms.CharField(required=True)
    participant = forms.CharField(required=True)
    sender = forms.CharField(required=False)
    comment = forms.CharField(required=False)

    def clean_participant(self):
        participant_id = self.cleaned_data['participant']
        try:
            participant = Participant.objects.get(
                participant_id=participant_id)
        except Participant.DoesNotExist:
            raise forms.ValidationError(
                _('Participant ID'), code='participant')
        return participant

    def clean(self):
        cleaned_data = super(BaseQuestionnaireForm, self).clean()
        errors = []
        for attribute in self.data.keys():
            if (
                self.fields.get(attribute, None) and
                isinstance(self.fields.get(attribute), forms.Field)
            ):
                continue
            else:
                errors.append(
                    forms.ValidationError(attribute, code='questions'))
        if errors:
            raise forms.ValidationError(errors)
        else:
            return cleaned_data

    def save(self):
        # FIXME
        pass


class EventSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(EventSelectionForm, self).__init__(*args, **kwargs)

        deployment = request.deployment if request else None

        self.fields['event'] = forms.ChoiceField(
            choices=Event.objects.filter(
                deployment=deployment,
            )
            .order_by('-end_date')
            .scalar('id', 'name')
        )
