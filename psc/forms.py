from django import forms
from models import VRChecklist, VRIncident, DCOChecklist, DCOIncident
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
