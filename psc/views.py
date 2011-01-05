# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from models import *
from datetime import datetime
from django.db.models import Q
from django.views.decorators.csrf import csrf_view_exempt
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rapidsms.contrib.messagelog.tables import MessageTable
from rapidsms.contrib.messagelog.models import Message
from forms import VRChecklistForm, VRIncidentForm, DCOIncidentForm, VRChecklistFilterForm

# paginator settings
items_per_page = 25

def home(request):
    return render_to_response('psc/layout.html')

@csrf_view_exempt
def vr_checklist_list(request):
    qs = Q()

    if request.method == 'GET':
        filter_form = VRChecklistFilterForm(request.GET)

        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data['zone']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['district']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__code__exact=data['district']).values_list('id', flat=True))
            if data['day']:
                qs &= Q(date=datetime.strptime(data['day'], '%d/%m/%Y'))
            if data['status']:
                pass
    else:
        filter_form = VRChecklistFilterForm()

    paginator = Paginator(VRChecklist.objects.filter(qs), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/vr_checklist_list.html', {'page_title': "Voter's Registration Data Management", 'checklists': checklists, 'filter_form': filter_form })

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

def vr_incident_update(request, incident_id=0):
    incident = get_object_or_404(VRIncident, pk=incident_id)
    if request.POST:        
        f = VRIncidentForm(request.POST, instance=incident)
        if f.is_valid():
            print f.cleaned_data
            f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_incident_list'))    
    else:
        f = VRIncidentForm(instance=incident)   
        return render_to_response('psc/vr_incident_update_form.html', {'page_title': 'Voters Registration Critrical Incidents', 'incident': incident, 'form': f })

def vr_incident_add(request):
    return render_to_response('psc/vr_incident_form.html')

def vr_incident_list(request):
    paginator = Paginator(VRIncident.objects.all(), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/vr_incident_list.html', {'page_title': "Voter's Registration Incidents", 'checklists': checklists})


def dco_list(request):
    paginator = Paginator(DCOChecklist.objects.all(), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/dco_checklist_list.html', {'checklists': checklists})

def dco_checklist(request, checklist_id=0):   
    if request.POST:
        gotcha = request.POST['PSC'];
        return HttpResponse(gotcha)
    else:
        return render_to_response('psc/dco_checklist_form.html', {'page_title': 'Display/Claims & Objections Checklist'}, context_instance=RequestContext(request))

def dco_incident(request, incident_id=0):
    return render_to_response('psc/dco_incident_form.html', {'page_title': 'Display/Claims & Objections Critical Incidents'})

def dco_incident_list(request):
    paginator = Paginator(DCOIncident.objects.all(), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/dco_incident_list.html', {'page_title': "DCO Incidents", 'checklists': checklists})

@csrf_view_exempt
def dco_incident_update(request, incident_id=0):
    
    incident = get_object_or_404(DCOIncident, pk=incident_id)
    if request.POST:
        f = DCOIncidentForm(request.POST, instance=incident)    
        f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_incident_list'))
    else:
        f = DCOIncidentForm(instance=incident)
        return render_to_response('psc/dco_incident_update_form.html', {'page_title': 'DCO Incidents', 'incident': incident, 'form': f })

@csrf_view_exempt
def dco_incident_add(request):
    if request.POST:
        f = DCOIncidentForm(request.POST)
        f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_incident_list'))
    else:
        f = DCOIncidentForm()
        return render_to_response('psc/dco_incident_add_form.html', {'page_title': 'Voters Registration Critrical Incidents', 'form': f })

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
