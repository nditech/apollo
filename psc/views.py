# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from models import *
from django.views.decorators.csrf import csrf_view_exempt
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rapidsms.contrib.messagelog.tables import MessageTable
from rapidsms.contrib.messagelog.models import Message
from forms import VRChecklistForm

# paginator settings
items_per_page = 25

def home(request):
    return render_to_response('psc/layout.html')

def vr_list(request):
    paginator = Paginator(VRChecklist.objects.all(), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/vr_checklist_list.html', {'checklists': checklists})

@csrf_view_exempt
def vr_checklist(request, checklist_id=0):
    checklist = get_object_or_404(VRChecklist, pk=checklist_id)
    if (request.POST):
        f = VRChecklistForm(request.POST, instance=checklist)
        f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_list'))
    else:
        f = VRChecklistForm(instance=checklist)
        return render_to_response('psc/vr_checklist_form.html', {'page_title': 'Voters Registration Checklist', 'checklist': checklist, 'form': f })

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

def message_log(request):
    messages =   MessageTable(Message.objects.all(), request=request)
    return render_to_response('psc/msg_log.html', { 'messages_list' : messages }, context_instance=RequestContext(request))

def action_log(request):
    #get action log for vr and dco 
    vr_checklist_log = VRChecklist.audit_log.all()
    vr_incident_log = VRIncident.audit_log.all()
    dco_checklist_log = DCOChecklist.audit_log.all()
    dco_incident_log = DCOIncident.audit_log.all()

    #all logs
    #logs = {'vr_checklist_log_list' : vr_checklist_log, 'vr_incident_log_list': vr_incident_log, 'dco_checklist_log_list': dco_checklist_log, 'dco_incident_log_list': dco_incident_log}

    return render_to_response('psc/action_log.html', {'vr_checklist_log_list' : vr_checklist_log, 'vr_incident_log_list': vr_incident_log, 'dco_checklist_log_list': dco_checklist_log, 'dco_incident_log_list': dco_incident_log})
