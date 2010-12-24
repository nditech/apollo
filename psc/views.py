# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext

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
    if request.POST:
        gotcha = request.POST['PSC'];
        return HttpResponse(gotcha)
    else:
        return render_to_response('psc/dco_checklist_form.html', {'page_title': 'Display/Claims & Objections Checklist'}, context_instance=RequestContext(request))

def dco_incident(request, incident_id=0):
    return render_to_response('psc/dco_incident_form.html', {'page_title': 'Display/Claims & Objections Critical Incidents'})

