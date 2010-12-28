# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext
from models import *
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rapidsms.contrib.messagelog.tables import MessageTable
from rapidsms.contrib.messagelog.models import Message

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

    return render_to_response('psc/psc_list.html', {'checklists': checklists})

def vr_checklist(request, checklist_id=0):
    checklist = get_object_or_404(VRChecklist, pk=checklist_id)
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

def message_log(request):
    messages =   MessageTable(Message.objects.all(), request=request)
    return render_to_response('psc/msg_log.html', { 'messages_list' : messages }, context_instance=RequestContext(request))
   