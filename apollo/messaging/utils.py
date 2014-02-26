from core.documents import Event, Form
from core.forms import BaseQuestionnaireForm
from django import forms

# returns: (prefix, participant_id, form_type, responses, comments)
parse_text = lambda text: (None, None, None, None, None)


def generate_questionnaire_from_message(request, sender, text):
    form_fields = {}
    (prefix, participant_id, form_type, responses, comments) = parse_text(text)
    events_in_deployment = Event.objects.filter(
        deployment=getattr(request, 'deployment'))
    form = Form.objects.filter(events__in=events_in_deployment,
                               prefix__iexact=prefix).first()
    if form:
        form_groups = []
        for group in form.groups:
            form_group = (group.name, {'fields': [], 'legend': group.name})
            for field in group.fields:
                if field.options:
                    if field.allows_multiple_values:
                        form_fields[field.name] = forms.MultipleChoiceField(
                            choices=field.options.items(), required=False,
                            help_text=field.description, label=field.name)
                    else:
                        form_fields[field.name] = forms.ChoiceField(
                            choices=field.options.items(), required=False,
                            help_text=field.description, label=field.name)
                else:
                    if form.form_type == u'CHECKLIST':
                        form_fields[field.name] = forms.IntegerField(
                            max_value=field.max_value or 9999,
                            min_value=field.min_value or 0, required=False,
                            help_text=field.description, label=field.name)
                    else:
                        form_fields[field.name] = forms.BooleanField(
                            required=False, help_text=field.description,
                            label=field.name, widget=forms.CheckboxInput())

                form_group[1]['fields'].append(field.name)
            form_groups.append(form_group)

    metaclass = type('Meta', (), {'fieldsets': form_groups})
    form_fields['Meta'] = metaclass
    # FIXME: This method should return an instantiated form with
    # parsed input
    return type('QuesationnaireForm', (BaseQuestionnaireForm,), form_fields)
