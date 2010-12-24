# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse

def home(request):
    return render_to_response('psc/layout.html')

def vr_list(request):
    return render_to_response('psc/psc_list.html')

def vr_checklist(request, checklist_id=0):
    return render_to_response('psc/vr_checklist_form.html', {'page_title': 'Voters Registration Checklist'})

def vr_incident(request, incident_id=0):
    return render_to_response('psc/vr_incident_form.html', {'page_title': 'Voters Registration Critrical Incidents'})

def dco_list(request):
    return HttpResponse('OK')

def dco_checklist(request, checklist_id=0):
    return render_to_response('psc/dco_checklist_form.html', {'page_title': 'Display & Claims Checklist'})

def dco_incident(request, incident_id=0):
    return render_to_response('psc/dco_incident_form.html', {'page_title': 'Display & Claims Critical Incidents'})

