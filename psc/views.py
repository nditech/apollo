# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse

def home(request):
    return render_to_response('psc/layout.html')

def vr_list(request):
    return render_to_response('psc/psc_list.html')

def vr_checklist(request, checklist_id=0):
    return HttpResponse('OK')

def vr_incident(request, incident_id=0):
    return HttpResponse('OK')

def dco_list(request):
    return HttpResponse('OK')

def dco_checklist(request, checklist_id=0):
    return HttpResponse('OK')

def dco_incident(request, incident_id=0):
    return HttpResponse('OK')

