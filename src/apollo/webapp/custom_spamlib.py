from dilla import spam
import string
import random
from models import *

@spam.strict_handler('webapp.Checklist.form')
def get_checklist_form(record, field):
    return ChecklistForm.objects.order_by('?')[0]

@spam.strict_handler('webapp.Checklist.location')
def get_checklist_location(record, field):
    return Location.objects.filter(type__name='Polling Stream').order_by('?')[0]

@spam.strict_handler('webapp.Checklist.observer')
def get_checklist_observer(record, field):
    return Contact.objects.filter(role__name="Monitor").order_by('?')[0]

@spam.strict_handler('webapp.Incident.form')
def get_incident_form(record, field):
    return IncidentForm.objects.order_by('?')[0]

@spam.strict_handler('webapp.Incident.location')
def get_incident_location(record, field):
    return Location.objects.filter(type__name='Polling Stream').order_by('?')[0]

@spam.strict_handler('webapp.Checklist.observer')
def get_incident_observer(record, field):
    return Contact.objects.order_by('?')[0]


