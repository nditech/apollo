from __future__ import unicode_literals
from django import forms
from core.documents import Event


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
