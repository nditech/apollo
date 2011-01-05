from django import forms
from models import VRChecklist, VRIncident, DCOChecklist, DCOIncident
from models import Zone, State, District
from django.forms.models import modelformset_factory
from datetime import datetime

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
            (1, 'no texts received'),
            (2, 'missing 1st text'),
            (3, 'missing 2nd text'),
            (4, 'missing 3rd text'),
            (5, 'missing any text'),
            (6, 'all texts received'))
VR_DAYS = (('', '--'),
        (datetime.date(datetime(2011, 1, 15)), 'Day 1'),
        (datetime.date(datetime(2011, 1, 20)), 'Day 2'),
        (datetime.date(datetime(2011, 1, 22)), 'Day 3'),
        (datetime.date(datetime(2011, 1, 27)), 'Day 4'),
        (datetime.date(datetime(2011, 1, 29)), 'Day 5'))

class VRChecklistFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="Observer Id", max_length=6, widget=forms.TextInput(attrs={'style':'width:7em'}))
    day = forms.ChoiceField(choices=VR_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False) 
    status = forms.ChoiceField(choices=STATUSES, required=False)
