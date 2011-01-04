from django import forms
from models import VRChecklist, VRIncident, DCOChecklist, DCOIncident
from models import Zone, State, District
from django.forms.models import modelformset_factory

class VRChecklistForm(forms.ModelForm):
    class Meta:
        model = VRChecklist
        exclude = ['location_type', 'location_id', 'location', 'observer', 'date']

class VRIncidentForm(forms.ModelForm):
    class Meta:
        model = VRIncident
        exclude = ['location_type', 'location_id', 'location', 'observer', 'date']

class DCOChecklistForm(forms.ModelForm):
    class Meta:
        model = DCOChecklist
        exclude = ['location_type', 'location_id', 'location', 'observer', 'date']

class DCOIncidentForm(forms.ModelForm):
    class Meta:
        model = DCOIncident
        exclude = ['location_type', 'location_id', 'location', 'observer', 'date']

DCOIncidentFormSet = modelformset_factory(DCOIncident)

ZONES = tuple([('', '--')]+[(zone.code, zone.name) for zone in Zone.objects.all()])
STATES = tuple([('', '--')]+[(state.code, state.name) for state in State.objects.all()])
DISTRICTS = tuple([('', '--')]+[(district.code, district.name) for district in District.objects.all()])
STATUSES = ((0, '--'),
            (1, '1st SMS complete'),
            (2, '2nd SMS complete'),
            (3, '3rd SMS complete'),
            (4, '1st SMS incomplete'),
            (5, '2nd SMS incomplete'),
            (6, '3rd SMS incomplete'),
            (7, '1st SMS missing'),
            (8, '2nd SMS missing'),
            (9, '3rd SMS missing'))
DAYS = (('', '--'),
        ('03/01/2011', 'Day 1'),
        ('10/01/2011', 'Day 2'),
        ('14/01/2011', 'Day 3'))

class VRChecklistFilterForm(forms.Form):
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False) 
    day = forms.ChoiceField(choices=DAYS, required=False)
    status = forms.ChoiceField(choices=STATUSES, required=False)
