from django import forms
from models import VRChecklist, VRIncident, DCOChecklist, DCOIncident, EDAYChecklist, EDAYIncident
from models import Zone, State, District, Observer, LGA, Sample
from django.forms.models import modelformset_factory
from datetime import datetime

ZONES = tuple([('', 'All')]+[(zone.code, zone.code) for zone in Zone.objects.all().order_by('name')])
STATES = tuple([('', 'All')]+[(state.code, state.name) for state in State.objects.all().order_by('name')])
DISTRICTS = tuple([('', 'All')]+[(district.code, district.name) for district in District.objects.all().order_by('name')])
LGAS = tuple([('', 'All')]+[(lga.code, lga.name) for lga in LGA.objects.all().order_by('name')])
SAMPLES = tuple([('', 'All')]+[(sample[0], sample[1]) for sample in Sample.SAMPLES])
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
        (datetime.date(datetime(2011, 1, 20)), 'Thu 20-Jan'),
        (datetime.date(datetime(2011, 1, 22)), 'Sat 22-Jan'),
        (datetime.date(datetime(2011, 1, 27)), 'Thu 27-Jan'),
        (datetime.date(datetime(2011, 1, 29)), 'Sat 29-Jan'),
        (datetime.date(datetime(2011, 2, 3)), 'Thu 03-Feb'),
        (datetime.date(datetime(2011, 2, 5)), 'Sat 05-Feb'))
EDAY_CHECKLIST_1ST = (('', 'All'),
                    (1, 'Complete'),
                    (2, 'Missing'))
EDAY_CHECKLIST_2ND = (('', 'All'),
                    (1, 'Complete'),
                    (5, 'Missing'),
                    (2, 'Partial'),
                    (3, 'Closed'),
                    (4, 'Problem'))
EDAY_CHECKLIST_3RD = (('', 'All'),
                    (1, 'Complete'),
                    (5, 'Missing'),
                    (2, 'Partial'),
                    (3, 'Closed'),
                    (4, 'Problem'))
EDAY_CHECKLIST_4TH = (('', 'All'),
                    (1, 'Complete'),
                    (5, 'Missing'),
                    (2, 'Partial'),
                    (3, 'Closed'),
                    (4, 'Problem'))
EDAY_CHECKLIST_5TH = (('', 'All'),
                    (1, 'Complete'),
                    (5, 'Missing'),
                    (2, 'Partial'),
                    (3, 'Closed'),
                    (4, 'Problem'))

EDAY_DAYS = (('', 'All'),
        (datetime.date(datetime(2011, 3, 31)), 'Thu 31-Mar'),
        (datetime.date(datetime(2011, 4, 2)), 'Sat 02-Apr'),
        (datetime.date(datetime(2011, 4, 7)), 'Thu 07-Apr'),
        (datetime.date(datetime(2011, 4, 9)), 'Sat 09-Apr'),
        (datetime.date(datetime(2011, 4, 16)), 'Sat 16-Apr'),
		(datetime.date(datetime(2011, 4, 26)), 'Tue 26-Apr'))

VR_INCIDENT_DAYS = tuple([('', 'All')]+[(date, date.strftime('%a %d-%b')) for date in VRIncident.objects.all().distinct('date').order_by('-date').values_list('date', flat=True)])

DCO_INCIDENT_DAYS = tuple([('', 'All')]+[(date, date.strftime('%a %d-%b')) for date in DCOIncident.objects.all().distinct('date').order_by('-date').values_list('date', flat=True)])

EDAY_INCIDENT_DAYS = tuple([('', 'All')]+[(date, date.strftime('%a %d-%b')) for date in EDAYIncident.objects.all().distinct('date').order_by('-date').values_list('date', flat=True)])

DCO_ARRIVAL = ((0, 'All'),
               (1, 'Arrived'),
               (2, 'Not Arrived'))
DCO_STATUS = ((0, 'All'),
              (1, 'Complete'),
              (2, 'Missing'),
              (3, 'Partial'),
              (4, 'Not Open Problem'),
              (5, 'Not Open'))
DCO_DAYS = (('', 'All'),
        (datetime.date(datetime(2011, 2, 14)), 'Mon 14-Feb'),
        (datetime.date(datetime(2011, 2, 17)), 'Thu 17-Feb'))

ROLES = (('', 'All'),
        ('NSC', 'NSC'),
        ('NS', 'NS'),
        ('ZC', 'ZC'),
        ('SC', 'SC'),
        ('SDC', 'SDC'),
        ('LGA', 'LGA'),
        ('OBS', 'OBS'))

PARTNERS = (('', 'All'),
            ('FOMWAN', 'FOMWAN'),
            ('JDPC', 'JDPC'),
            ('NBA', 'NBA'),
            ('TMC', 'TMC'))

vr_checklist_dates =  list(VRChecklist.objects.all().distinct('date').values_list('date', flat=True).order_by('date'))
dco_checklist_dates = list(DCOChecklist.objects.all().distinct('date').values_list('date', flat=True).order_by('date'))
eday_checklist_dates =  list(EDAYChecklist.objects.all().distinct('date').values_list('date', flat=True).order_by('date'))
checklist_dates = vr_checklist_dates + dco_checklist_dates + eday_checklist_dates

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

class EDAYChecklistForm(forms.ModelForm):
    class Meta:
        model = EDAYChecklist
        exclude = ['location_type', 'location', 'location_id', 'observer', 'date', 'checklist_index', 'sms_status_5th', 'audit_log']

class EDAYIncidentForm(forms.ModelForm):
    date = forms.ChoiceField(choices=tuple([('', '--')] + [(date, label) for (date, label) in EDAY_DAYS if date]))
    observer = forms.ModelChoiceField(queryset=Observer.objects.filter(role__in=['SC', 'SDC', 'LGA']).exclude(observer_id=""), empty_label="--")
    class Meta:
        model = EDAYIncident
        exclude = ['location_type', 'location_id', 'location']
        
class EDAYIncidentUpdateForm(forms.ModelForm):
    observer = forms.ModelChoiceField(queryset=Observer.objects.exclude(observer_id=""), empty_label="--")
    class Meta:
        model = EDAYIncident
        exclude = ['location_type', 'location_id', 'location', 'date']

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
    first = forms.ChoiceField(choices=DCO_ARRIVAL, required=False, label='Arrival Text')
    second = forms.ChoiceField(choices=DCO_STATUS, required=False, label='2nd SMS')
    
class EDAYChecklistFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=EDAY_DAYS, required=False)
    sample = forms.ChoiceField(choices=SAMPLES, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    first = forms.ChoiceField(choices=EDAY_CHECKLIST_1ST, required=False, label='1st SMS')
    second = forms.ChoiceField(choices=EDAY_CHECKLIST_2ND, required=False, label='2nd SMS')
    third = forms.ChoiceField(choices=EDAY_CHECKLIST_3RD, required=False, label='3rd SMS')
    fourth = forms.ChoiceField(choices=EDAY_CHECKLIST_4TH, required=False, label='4th SMS')
    fifth = forms.ChoiceField(choices=EDAY_CHECKLIST_5TH, required=False, label='5th SMS')
    
class ContactlistFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False, label='District')
    lga = forms.ChoiceField(choices=LGAS, required=False, label='LGA')
    role = forms.ChoiceField(choices=ROLES, required=False, label='Role')
    partner = forms.ChoiceField(choices=PARTNERS, required=False, label='Partner')

class VRIncidentFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=VR_INCIDENT_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False)

class DCOIncidentFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=DCO_INCIDENT_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False)

class EDAYIncidentFilterForm(forms.Form):
    observer_id = forms.CharField(required=False, label="PSC ID", max_length=6, widget=forms.TextInput(attrs={'autocomplete':'off','style':'width:7em'}))
    day = forms.ChoiceField(choices=EDAY_DAYS, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    district = forms.ChoiceField(choices=DISTRICTS, required=False)

class MessagelogFilterForm(forms.Form):
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))
    message = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))

class DashboardFilterForm(forms.Form):
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    sample = forms.ChoiceField(choices=SAMPLES, required=False)
    date = forms.ChoiceField(choices=checklist_date_choices, required=False)

class VRAnalysisFilterForm(forms.Form):
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    date = forms.ChoiceField(choices=VR_DAYS, required=False)
    
class EDAYAnalysisFilterForm(forms.Form):
    sample = forms.ChoiceField(choices=SAMPLES, required=False)
    zone = forms.ChoiceField(choices=ZONES, required=False)
    state = forms.ChoiceField(choices=STATES, required=False)
    date = forms.ChoiceField(choices=EDAY_DAYS, required=False)

class VRSummaryFilterForm(forms.Form):
    date = forms.ChoiceField(choices=tuple([('', 'Today')] + [(date, label) for (date, label) in VR_DAYS if date]))

class DCOSummaryFilterForm(forms.Form):
    date = forms.ChoiceField(choices=tuple([('', 'Today')] + [(date, label) for (date, label) in DCO_DAYS if date]))

class EDAYSummaryFilterForm(forms.Form):
    date = forms.ChoiceField(choices=tuple([('', 'Today')] + [(date, label) for (date, label) in EDAY_DAYS if date]))

class EmailBlastForm(forms.Form):
    subject = forms.CharField(max_length=500)
    recipient = forms.MultipleChoiceField(choices=ROLES, required=False)
    psc_id  = forms.CharField(max_length=10)
    message = forms.CharField(widget=forms.Textarea)
    
class ContactEditForm(forms.ModelForm):
    class Meta:
        model = Observer
        exclude = ['dob', 'location_type', 'observer_id', 'role', 'location_id', 'location', 'supervisor', 'contact', 'name', 'position']
