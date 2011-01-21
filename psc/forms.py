from django import forms
from models import VRChecklist, VRIncident, DCOChecklist, DCOIncident
from models import Zone, State, District, Observer
from django.forms.models import modelformset_factory
from datetime import datetime

ZONES = tuple([('', 'All')]+[(zone.code, zone.code) for zone in Zone.objects.all().order_by('name')])
STATES = tuple([('', 'All')]+[(state.code, state.name) for state in State.objects.all().order_by('name')])
DISTRICTS = tuple([('', 'All')]+[(district.code, district.name) for district in District.objects.all().order_by('name')])
STATUSES = ((0, 'All'),
            (1, 'no texts received'),
            (2, 'missing 1st text'),
            (3, 'missing 2nd text'),
            (4, 'missing 3rd text'),
            (5, 'missing any text'),
            (6, 'received 1st text'),
            (7, 'received 2nd text'),
            (8, 'received 3rd text'),
            (9, 'all texts received'))
VR_CHECKLIST_1ST = ((0, 'All'),
                    (1, 'Complete'),
                    (2, 'Missing'))
VR_CHECKLIST_2ND = ((0, 'All'),
                    (1, 'Complete'),
                    (2, 'Missing'),
                    (3, 'Partial'),
                    (4, 'Not Open Problem'),
                    (5, 'Not Open'))
VR_CHECKLIST_3RD = ((0, 'All'),
                    (1, 'Complete'),
                    (2, 'Missing'),
                    (3, 'Partial'),
                    (4, 'Not Open Problem'),
                    (5, 'Not Open'),
                    (6, 'Blank'))
VR_DAYS = (('', 'All'),
        (datetime.date(datetime(2011, 1, 15)), 'Sat 15-Jan'),
        (datetime.date(datetime(2011, 1, 19)), 'Wed 19-Jan'),
        (datetime.date(datetime(2011, 1, 20)), 'Thu 20-Jan'),
        (datetime.date(datetime(2011, 1, 22)), 'Sat 22-Jan'),
        (datetime.date(datetime(2011, 1, 27)), 'Thu 27-Jan'),
        (datetime.date(datetime(2011, 1, 29)), 'Sat 29-Jan'))

DCO_DAYS = (('', 'All'),
        (datetime.date(datetime(2011, 2, 3)), 'Thu 3-Feb'),
        (datetime.date(datetime(2011, 2, 8)), 'Tue 8-Feb'))

vr_checklist_dates =  list(VRChecklist.objects.all().distinct('date').values_list('date', flat=True).order_by('date'))
dco_checklist_dates = list(DCOChecklist.objects.all().distinct('date').values_list('date', flat=True).order_by('date'))
checklist_dates = vr_checklist_dates + dco_checklist_dates

# make the checklist dates unique
checklist_dates = list(set(checklist_dates))
checklist_dates.sort()
checklist_date_choices = [[datetime.date(datetime.today()), 'Today']]

for checklist_date in checklist_dates:
    checklist_date_choices.append((checklist_date, checklist_date.strftime('%Y %d-%b %a')))

checklist_date_choices = tuple(checklist_date_choices)

class VRChecklistForm(forms.ModelForm):
    class Meta:
        model = VRChecklist
        exclude = ['location_type', 'location', 'observer', 'date']

class VRIncidentForm(forms.ModelForm):
    date = forms.ChoiceField(choices=tuple([('', '--')] + [(date, label) for (date, label) in VR_DAYS if date]))
    observer = forms.ModelChoiceField(queryset=Observer.objects.filter(role__in=['SC', 'SDC', 'LGA']).exclude(observer_id=""), empty_label="--")
    class Meta:
        model = VRIncident
        exclude = ['location_type', 'location_id', 'location']

class VRIncidentUpdateForm(forms.ModelForm):
    observer = forms.ModelChoiceField(queryset=Observer.objects.exclude(observer_id=""), empty_label="--")
    class Meta:
        model = VRIncident
        exclude = ['location_type', 'location_id', 'location']

class DCOChecklistForm(forms.ModelForm):
    class Meta:
        model = DCOChecklist
        exclude = ['location_type', 'location', 'observer', 'date']

class DCOIncidentForm(forms.ModelForm):
    date = forms.ChoiceField(choices=tuple([('', '--')] + [(date, label) for (date, label) in DCO_DAYS if date]))
    observer = forms.ModelChoiceField(queryset=Observer.objects.filter(role__in=['SC', 'SDC', 'LGA']).exclude(observer_id=""), empty_label="--")
    class Meta:
        model = DCOIncident
        exclude = ['location_type', 'location_id', 'location']

class DCOIncidentUpdateForm(forms.ModelForm):
    observer = forms.ModelChoiceField(queryset=Observer.objects.exclude(observer_id=""), empty_label="--")
    class Meta:
        model = DCOIncident
        exclude = ['location_type', 'location_id', 'location']

DCOIncidentFormSet = modelformset_factory(DCOIncident)

class VRChecklistFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em',}))
    day = forms.ChoiceField(choices=VR_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    first = forms.ChoiceField(choices=VR_CHECKLIST_1ST, required=False, label='1st SMS')
    second = forms.ChoiceField(choices=VR_CHECKLIST_2ND, required=False, label='2nd SMS')
    third = forms.ChoiceField(choices=VR_CHECKLIST_3RD, required=False, label='3rd SMS')

class DCOChecklistFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=DCO_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False) 

class VRIncidentFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=VR_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False)

class DCOIncidentFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=VR_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False)

class MessagelogFilterForm(forms.Form):
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))
    message = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))

class DashboardFilterForm(forms.Form):
    zone = forms.ChoiceField(choices=ZONES, required=False)
    date = forms.ChoiceField(choices=checklist_date_choices, required=False)
