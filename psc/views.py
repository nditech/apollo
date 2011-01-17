# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from models import *
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rapidsms.contrib.messagelog.tables import MessageTable
from rapidsms.contrib.messagelog.models import Message
from forms import VRChecklistForm, VRIncidentForm, DCOIncidentForm, VRChecklistFilterForm, VRIncidentFilterForm, DCOIncidentFilterForm, DCOChecklistFilterForm, DCOChecklistForm, VR_DAYS, DCO_DAYS
from forms import DCOIncidentUpdateForm, VRIncidentUpdateForm
from datetime import datetime
from django.contrib.auth.decorators import login_required

# paginator settings
items_per_page = 25

@login_required()
def home(request):
    context = {'page_title': 'PSC 2011 SwiftCount Dashboard'}
    
    #vr first missing sms
    context['missing_first_sms'] = VRChecklist.objects.filter(submitted=False).count()
    # second missing sms
    qs2 = Q(A__isnull=True) | Q(B=0) | Q(C__isnull=True) | Q(F__isnull=True) | Q(G=0) | \
                          (Q(D1__isnull=True) & Q(D2__isnull=True) & Q(D3__isnull=True) & Q(D4__isnull=True)) | \
                          (Q(E1__isnull=True) & Q(E2__isnull=True) & Q(E3__isnull=True) & Q(E4__isnull=True) & \
                          Q(E5__isnull=True))
    context['missing_second_sms'] = VRChecklist.objects.filter(qs2).count()
    # third missing sms
    qs3 = Q(H__isnull=True) | Q(J__isnull=True) | Q(K__isnull=True) | Q(M__isnull=True) | \
                          Q(N__isnull=True) | Q(P__isnull=True) | Q(Q__isnull=True) | Q(R__isnull=True) | \
                          Q(S__isnull=True) | Q(T=0) | Q(U=0) | Q(V=0) | Q(W=0) | Q(X=0) | Q(Y__isnull=True) | \
                          Q(Z__isnull=True) | Q(AA__isnull=True)
    context['missing_third_sms'] = VRChecklist.objects.filter(qs3).count()

    #dco
    #checklist sent today
    context['checklist_today'] = DCOChecklist.objects.filter(date=datetime.now()).count()
    context['dco_in_count'] = DCOIncident.objects.all().count()
    dco_d = DCOIncident.objects.all()
    
    
    


    #render
    return render_to_response('psc/home.html', context,  context_instance=RequestContext(request))

@login_required()
def vr_checklist_list(request):
    qs = Q(date__in=[d[0] for d in VR_DAYS if d[0]])
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
                qs &= Q(date=data['day'])
            if data['status']:
                if int(data['status']) == 1 or int(data['status']) == 2: # no texts received or missing first text
                    qs &= Q(submitted=False)
                elif int(data['status']) == 3: # missing second text
                    qs &= Q(A__isnull=True) | Q(B=0) | Q(C__isnull=True) | Q(F__isnull=True) | Q(G=0) | \
                          (Q(D1__isnull=True) & Q(D2__isnull=True) & Q(D3__isnull=True) & Q(D4__isnull=True)) | \
                          (Q(E1__isnull=True) & Q(E2__isnull=True) & Q(E3__isnull=True) & Q(E4__isnull=True) & \
                          Q(E5__isnull=True))
                elif int(data['status']) == 4: # missing third text
                    qs &= Q(H__isnull=True) | Q(J__isnull=True) | Q(K__isnull=True) | Q(M__isnull=True) | \
                          Q(N__isnull=True) | Q(P__isnull=True) | Q(Q__isnull=True) | Q(R__isnull=True) | \
                          Q(S__isnull=True) | Q(T=0) | Q(U=0) | Q(V=0) | Q(W=0) | Q(X=0) | Q(Y__isnull=True) | \
                          Q(Z__isnull=True) | Q(AA__isnull=True)
                elif int(data['status']) == 5: # missing any text
                    qs &= Q(submitted=False) | Q(A__isnull=True) | Q(B=0) | Q(C__isnull=True) | \
                          Q(F__isnull=True) | Q(G=0) | \
                          (Q(D1__isnull=True) & Q(D2__isnull=True) & Q(D3__isnull=True) & Q(D4__isnull=True)) | \
                          (Q(E1__isnull=True) & Q(E2__isnull=True) & Q(E3__isnull=True) & Q(E4__isnull=True) & \
                          Q(E5__isnull=True)) | Q(H__isnull=True) | Q(J__isnull=True) | Q(K__isnull=True) | \
                          Q(M__isnull=True) | Q(N__isnull=True) | Q(P__isnull=True) | Q(Q__isnull=True) | \
                          Q(R__isnull=True) | Q(S__isnull=True) | Q(T=0) | Q(U=0) | Q(V=0) | Q(W=0) | \
                          Q(X=0) | Q(Y__isnull=True) | Q(Z__isnull=True) | Q(AA__isnull=True)
                elif int(data['status']) == 6: # all texts received
                    qs &= Q(submitted=True,A__isnull=False,B__gte=1,C__isnull=False,F__isnull=False,G__gte=1) & \
                          Q(H__isnull=False,J__isnull=False,K__isnull=False,M__isnull=False,N__isnull=False) & \
                          Q(P__isnull=False,Q__isnull=False,R__isnull=False,S__isnull=False,T__gte=1,U__gte=1) & \
                          Q(V__gte=1,W__gte=1,X__gte=1,Y__isnull=False,Z__isnull=False,AA__isnull=False) & \
                          (Q(D1__isnull=False) | \
                          Q(D2__isnull=False) | \
                          Q(D3__isnull=False) | \
                          Q(D4__isnull=False)) & \
                          (Q(E1__isnull=False) | \
                          Q(E2__isnull=False) | \
                          Q(E3__isnull=False) | \
                          Q(E4__isnull=False) | \
                          Q(E5__isnull=False))
            if data['observer_id']:
                qs &= Q(observer__observer_id__exact=data['observer_id'])
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

    return render_to_response('psc/vr_checklist_list.html', {'page_title': "Voter Registration Data Management", 'checklists': checklists, 'filter_form': filter_form }, context_instance=RequestContext(request))

@login_required()
def dco_checklist_list(request):
    qs = Q(date__in=[d[0] for d in DCO_DAYS if d[0]])    
    if request.method == 'GET':
        filter_form = DCOChecklistFilterForm(request.GET)

        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data['zone']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['district']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__code__exact=data['district']).values_list('id', flat=True))
            if data['day']:
                qs &= Q(date=data['day'])
            if data['observer_id']:
                qs &= Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = DCOChecklistFilterForm()

    paginator = Paginator(DCOChecklist.objects.filter(qs).order_by('date', 'observer', 'sms_serial'), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/dco_checklist_list.html', {'page_title': "Display, Claims & Objections Data Management", 'checklists': checklists, 'filter_form': filter_form }, context_instance=RequestContext(request))

@login_required()
def vr_checklist(request, checklist_id=0):
    checklist = get_object_or_404(VRChecklist, pk=checklist_id)
    location = checklist.observer.location
    if (request.POST):
        f = VRChecklistForm(request.POST, instance=checklist)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_checklist_list'))
    else:
        f = VRChecklistForm(instance=checklist)
        return render_to_response('psc/vr_checklist_form.html', {'page_title': "Voter Registration Checklist", 'checklist': checklist, 'location': location, 'form': f }, context_instance=RequestContext(request))

@login_required()
def dco_checklist(request, checklist_id=0):   
    checklist = get_object_or_404(DCOChecklist, pk=checklist_id)
    location = checklist.observer.location
    if (request.POST):
        f = DCOChecklistForm(request.POST, instance=checklist)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_checklist_list'))
    else:
        f = DCOChecklistForm(instance=checklist)
    return render_to_response('psc/dco_checklist_form.html', {'page_title': 'Display, Claims & Objections Checklist', 'checklist': checklist, 'location': location, 'form': f}, context_instance=RequestContext(request))

@login_required()
def vr_incident_update(request, incident_id=0):
    incident = get_object_or_404(VRIncident, pk=incident_id)
    location = incident.observer.location
    if request.POST:        
        f = VRIncidentUpdateForm(request.POST, instance=incident)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_incident_list'))    
    else:
        f = VRIncidentForm(instance=incident)   
        return render_to_response('psc/vr_incident_update_form.html', {'page_title': "Voter Registration Critrical Incident", 'incident': incident, 'location': location, 'form': f }, context_instance=RequestContext(request))

@login_required()
def dco_incident_update(request, incident_id=0):
    incident = get_object_or_404(DCOIncident, pk=incident_id)
    location = incident.observer.location
    if request.POST:
        f = DCOIncidentUpdateForm(request.POST, instance=incident)    
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_incident_list'))
    else:
        f = DCOIncidentForm(instance=incident)
        return render_to_response('psc/dco_incident_update_form.html', {'page_title': 'Display, Claims & Objections Critical Incident', 'incident': incident, 'location': location, 'form': f }, context_instance=RequestContext(request))

@login_required()
def vr_incident_add(request):
    if request.POST:
        f = VRIncidentForm(request.POST, VRIncident)
        f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_incident_list'))
    else:
        f = VRIncidentForm()
        return render_to_response('psc/vr_incident_add_form.html', {'page_title': "Add Voter Registration Critrical Incident", 'form': f }, context_instance=RequestContext(request))

@login_required()
def dco_incident_add(request):
    if request.POST:
        f = DCOIncidentForm(request.POST)                    
        f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_incident_list'))
    else:
        f = DCOIncidentForm()
        return render_to_response('psc/dco_incident_add_form.html', {'page_title': "Add Display, Claims & Objections Critrical Incident", 'form': f }, context_instance=RequestContext(request))

@login_required()
def vr_incident_list(request):
    qs = Q()

    if request.method == 'GET':
        filter_form = VRIncidentFilterForm(request.GET)

        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data['zone']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['district']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__code__exact=data['district']).values_list('id', flat=True))
            if data['day']:
                qs &= Q(date=data['day'])
            if data['observer_id']:
                qs &= Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = VRIncidentFilterForm()
    
    paginator = Paginator(VRIncident.objects.filter(qs).order_by('-id'), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/vr_incident_list.html', {'page_title': "Voter Registration Critical Incidents", 'checklists': checklists, 'filter_form': filter_form}, context_instance=RequestContext(request))

@login_required()
def dco_incident_list(request):
    qs = Q()
    if request.method == 'GET':
        filter_form = DCOIncidentFilterForm(request.GET)

        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data['zone']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['district']:
                qs &= Q(observer__location_id__in=LGA.objects.filter(parent__code__exact=data['district']).values_list('id', flat=True))
            if data['day']:
                qs &= Q(date=data['day'])
            if data['observer_id']:
                qs &= Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = DCOIncidentFilterForm()

    paginator = Paginator(DCOIncident.objects.filter(qs).order_by('-id'), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    return render_to_response('psc/dco_incident_list.html', {'page_title': "Display, Claims & Objections Critical Incidents", 'checklists': checklists, 'filter_form': filter_form}, context_instance=RequestContext(request))

@login_required()
def message_log(request):
    messages = MessageTable(Message.objects.all(), request=request)
    return render_to_response('psc/msg_log.html', { 'page_title': 'Message Log', 'messages_list' : messages }, context_instance=RequestContext(request))

@login_required()
def action_log(request):
    from itertools import chain
    #get action log for vr and dco 
    vr_checklist_log = VRChecklist.audit_log.all()
    vr_incident_log = VRIncident.audit_log.all()
    dco_checklist_log = DCOChecklist.audit_log.all()
    dco_incident_log = DCOIncident.audit_log.all()

    object_list = list(chain(dco_checklist_log, dco_incident_log, vr_incident_log, vr_checklist_log))
    
    paginator = Paginator(object_list, items_per_page)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        logs = paginator.page(page)
    except (EmptyPage, InvalidPage):
        logs = paginator.page(paginator.num_pages)
    print logs
    return render_to_response('psc/action_log.html', {'page_title': 'Action Log', 'logs' : logs},  context_instance=RequestContext(request))
