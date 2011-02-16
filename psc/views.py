# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from models import *
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rapidsms.contrib.messagelog.tables import MessageTable
from rapidsms.contrib.messagelog.models import Message
from forms import VRChecklistForm, VRIncidentForm, DCOIncidentForm, VRChecklistFilterForm, VRIncidentFilterForm, DCOIncidentFilterForm, DCOChecklistFilterForm, DCOChecklistForm
from forms import VR_DAYS
from forms import DCOIncidentUpdateForm, VRIncidentUpdateForm, MessagelogFilterForm, DashboardFilterForm, VRAnalysisFilterForm
from forms import VRSummaryFilterForm, DCOSummaryFilterForm, EmailBlastForm
from datetime import datetime
from django.core import serializers
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, permission_required
import stats
from queries import queries

# paginator settings
items_per_page = 25

@login_required()
def home(request):
    filter_date = datetime.date(datetime.today())
    qs = Q()
    if not request.session.has_key('dashboard_filter'):
        request.session['dashboard_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'date']):
            request.session['dashboard_filter'] = request.GET
        filter_form = DashboardFilterForm(request.session['dashboard_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['zone']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__parent__parent__code__iexact=data['zone']).values('id'))
            if data['date']:
                filter_date = datetime.date(datetime.strptime(data['date'], '%Y-%m-%d'))
    else:
        filter_form = DashboardFilterForm()
    qs = Q(date=filter_date) & qs

    context = {'page_title': 'PSC 2011 SwiftCount Dashboard'}
    context['filter_form'] = filter_form


    #vr first missing sms
    context['missing_first_sms'] = stats.model_sieve(VRChecklist, ['submitted'], exclude=True).filter(qs).count()
    context['received_first_sms'] = stats.model_sieve(VRChecklist, ['submitted']).filter(qs).count()




    # second missing sms
    context['complete_second_sms'] = stats.model_sieve(VRChecklist, ['A', 'B', 'C', 'F', 'G', ['D1', 'D2', 'D3', 'D4'], ['E1', 'E2', 'E3', 'E4', 'E5']]).filter(A__in=[1,2,3]).filter(qs).count()
    
    qs_partial_include = Q(A__lt=4) | Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
          Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
          Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
          Q(E5__isnull=False)
    qs_partial_exclude = Q(A__in=[1,2,3,4]) & Q(B__gt=0) & Q(C__isnull=False) & Q(F__isnull=False) & Q(G__gt=0) & \
          (Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)) & \
          (Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
          Q(E5__isnull=False))
    context['incomplete_second_sms'] = VRChecklist.objects.filter(qs_partial_include).exclude(qs_partial_exclude).filter(qs).count()

    qs_unverified = (Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
          Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
          Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
          Q(E5__isnull=False)) & Q(A=4) & Q(verified_second=False)
    context['unverified_second_sms'] = VRChecklist.objects.filter(qs_unverified).filter(qs).count()
    
    qs_not_open = (Q(A=4) & Q(verified_second=True)) | ((Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & \
          (Q(D1__isnull=True) | Q(D2__isnull=True) | Q(D3__isnull=True) | Q(D4__isnull=True)) & \
          (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | \
          Q(E5__isnull=True))) & Q(A=4))
    context['not_open_second_sms'] = VRChecklist.objects.filter(qs_not_open).filter(qs).count()

    qs_missing = Q(A__isnull=True) & Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & (Q(D1__isnull=True) | Q(D2__isnull=True) | \
        Q(D3__isnull=True) | Q(D4__isnull=True)) & (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | Q(E5__isnull=True))
    
    context['missing_second_sms'] = VRChecklist.objects.filter(qs_missing).filter(qs).count()





    qs_complete = Q(H__isnull=False) & Q(J__isnull=False) & Q(K__isnull=False) & Q(M__isnull=False) & \
              Q(N__isnull=False) & Q(P__isnull=False) & Q(Q__isnull=False) & Q(R__isnull=False) & \
              Q(S__isnull=False) & Q(T__gt=0) & Q(U__gt=0) & Q(V__gt=0) & Q(W__gt=0) & Q(X__gt=0) & Q(Y__isnull=False) & \
              Q(Z__isnull=False) & Q(AA__isnull=False)
    qs_missing = Q(H__isnull=True) & Q(J__isnull=True) & Q(K__isnull=True) & Q(M__isnull=True) & \
              Q(N__isnull=True) & Q(P__isnull=True) & Q(Q__isnull=True) & Q(R__isnull=True) & \
              Q(S__isnull=True) & Q(T=0) & Q(U=0) & Q(V=0) & Q(W=0) & Q(X=0) & Q(Y__isnull=True) & \
              Q(Z__isnull=True) & Q(AA__isnull=True)
    qs_partial = (Q(H__isnull=False) | Q(J__isnull=False) | Q(K__isnull=False) | Q(M__isnull=False) | \
              Q(N__isnull=False) | Q(P__isnull=False) | Q(Q__isnull=False) | Q(R__isnull=False) | \
              Q(S__isnull=False) | Q(T__gt=0) | Q(U__gt=0) | Q(V__gt=0) | Q(W__gt=0) | Q(X__gt=0) | Q(Y__isnull=False) | \
              Q(Z__isnull=False) | Q(AA__isnull=False)) & ~(qs_complete)
    qs_third_complete = ~Q(A=4) & qs_complete
    qs_third_missing = ~Q(A=4) & qs_missing
    qs_third_partial = ~Q(A=4) & qs_partial
    qs_third_problem = ((Q(A=4) & qs_partial) | (Q(A=4) & qs_complete & Q(verified_third=False)))
    qs_third_verified = ((Q(A=4) & Q(verified_third=True) & qs_partial))
    qs_third_blank = Q(A=4) & qs_missing
    # third missing sms
    context['complete_third_sms'] = VRChecklist.objects.filter(qs_third_complete).filter(qs).count()
    context['blank_third_sms'] = VRChecklist.objects.filter(qs_third_blank).filter(qs).count()
    context['partial_third_sms'] = VRChecklist.objects.filter(qs).filter(qs_third_partial).count()
    context['unverified_third_sms'] = VRChecklist.objects.filter(qs).filter(qs_third_problem).count()
    context['not_open_third_sms'] = VRChecklist.objects.filter(qs_third_verified).filter(qs).count()
    context['missing_third_sms'] = VRChecklist.objects.filter(qs_third_missing).filter(qs).count()

    context['vr_incidents_count'] = VRIncident.objects.all().count()
    context['vr_incidents_today'] = VRIncident.objects.filter(qs).count()

    #dco checklist sent today
    qs_dco_arrived = Q(submitted=True)
    qs_dco_not_arrived = Q(submitted=False) 
    context['dco_arrived'] = DCOChecklist.objects.filter(qs).filter(qs_dco_arrived).count()
    context['dco_not_arrived'] = DCOChecklist.objects.filter(qs).filter(qs_dco_not_arrived).count()

    context['dco_missing'] = DCOChecklist.objects.filter(qs).filter(queries['dco']['status']['missing']).count()
    context['dco_not_open_problem'] = DCOChecklist.objects.filter(qs).filter(queries['dco']['status']['problem']).count()
    context['dco_partial'] = DCOChecklist.objects.filter(qs).filter(queries['dco']['status']['partial']).count()
    context['dco_not_open'] = DCOChecklist.objects.filter(qs).filter(queries['dco']['status']['not_open']).count()
    context['dco_complete'] = DCOChecklist.objects.filter(qs).filter(queries['dco']['status']['complete']).count()

    context['dco_incidents_count'] = DCOIncident.objects.all().count()
    context['dco_incidents_today'] = DCOIncident.objects.filter(qs).count()

    context['dco_checklists_today'] = DCOChecklist.objects.filter(qs).count()

    #render
    return render_to_response('psc/home.html', context,  context_instance=RequestContext(request))

@login_required()
def vr_checklist_list(request):
    #qs = Q(date__in=[d[0] for d in VR_DAYS if d[0]])
    qs_include = Q()
    qs_exclude = Q()
    if not request.session.has_key('vr_checklist_filter'):
        request.session['vr_checklist_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'state', 'first', 'second', 'third', 'day', 'observer_id']):
            request.session['vr_checklist_filter'] = request.GET
        filter_form = VRChecklistFilterForm(request.session['vr_checklist_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['zone']:
                qs_include &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs_include &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['day']:
                qs_include &= Q(date=data['day'])

            if data['first'] == u'1':
                qs_include &= Q(submitted=True)
            elif data['first'] == u'2':
                qs_include &= Q(submitted=False)

            if data['second'] == u'1': # complete
                qs_include &= Q(A__in=[1,2,3]) & Q(B__gt=0) & Q(C__isnull=False) & Q(F__isnull=False) & Q(G__gt=0) & \
                      (Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)) & \
                      (Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
                      Q(E5__isnull=False))
            elif data['second'] == u'2': # missing
                qs_include &= Q(A__isnull=True) & Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & \
                      (Q(D1__isnull=True) | Q(D2__isnull=True) | Q(D3__isnull=True) | Q(D4__isnull=True)) & \
                      (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | \
                      Q(E5__isnull=True))
            elif data['second'] == u'3': # partial
                qs_include &= Q(A__lt=4) | Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
                      Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
                      Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
                      Q(E5__isnull=False)
                qs_exclude &= Q(A__in=[1,2,3,4]) & Q(B__gt=0) & Q(C__isnull=False) & Q(F__isnull=False) & Q(G__gt=0) & \
                      (Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)) & \
                      (Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
                      Q(E5__isnull=False))
            elif data['second'] == u'4': # not open unverified
                qs_include &= (Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
                      Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
                      Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
                      Q(E5__isnull=False)) & Q(A=4) & Q(verified_second=False)
            elif data['second'] == u'5': # not open verified
                qs_include &= (Q(A=4) & Q(verified_second=True)) | ((Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & \
                      (Q(D1__isnull=True) | Q(D2__isnull=True) | Q(D3__isnull=True) | Q(D4__isnull=True)) & \
                      (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | \
                      Q(E5__isnull=True))) & Q(A=4))

            qs_complete = Q(H__isnull=False) & Q(J__isnull=False) & Q(K__isnull=False) & Q(M__isnull=False) & \
                      Q(N__isnull=False) & Q(P__isnull=False) & Q(Q__isnull=False) & Q(R__isnull=False) & \
                      Q(S__isnull=False) & Q(T__gt=0) & Q(U__gt=0) & Q(V__gt=0) & Q(W__gt=0) & Q(X__gt=0) & Q(Y__isnull=False) & \
                      Q(Z__isnull=False) & Q(AA__isnull=False)
            qs_missing = Q(H__isnull=True) & Q(J__isnull=True) & Q(K__isnull=True) & Q(M__isnull=True) & \
                      Q(N__isnull=True) & Q(P__isnull=True) & Q(Q__isnull=True) & Q(R__isnull=True) & \
                      Q(S__isnull=True) & Q(T=0) & Q(U=0) & Q(V=0) & Q(W=0) & Q(X=0) & Q(Y__isnull=True) & \
                      Q(Z__isnull=True) & Q(AA__isnull=True)
            qs_partial = (Q(H__isnull=False) | Q(J__isnull=False) | Q(K__isnull=False) | Q(M__isnull=False) | \
                      Q(N__isnull=False) | Q(P__isnull=False) | Q(Q__isnull=False) | Q(R__isnull=False) | \
                      Q(S__isnull=False) | Q(T__gt=0) | Q(U__gt=0) | Q(V__gt=0) | Q(W__gt=0) | Q(X__gt=0) | Q(Y__isnull=False) | \
                      Q(Z__isnull=False) | Q(AA__isnull=False)) & ~(qs_complete)
            if data['third'] == u'1': # complete
                qs_include &= ~Q(A=4) & qs_complete
            elif data['third'] == u'2': # missing
                qs_include &= ~Q(A=4) & qs_missing
            elif data['third'] == u'3': # partial
                qs_include &= ~Q(A=4) & qs_partial
            elif data['third'] == u'4': # not open unverified
                qs_include &= ((Q(A=4) & qs_partial) | (Q(A=4) & qs_complete & Q(verified_third=False)))
            elif data['third'] == u'5': # not open verified
                qs_include &= ((Q(A=4) & Q(verified_third=True) & qs_partial))
            elif data['third'] == u'6': # blank
                qs_include &= Q(A=4) & qs_missing
            
            if data['observer_id']:
                qs_include = Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = VRChecklistFilterForm()

    #get all objects
    global items_per_page
    if request.GET.get('export'):
	    items_per_page = VRChecklist.objects.filter(qs_include).exclude(qs_exclude).count()
    
    paginator = Paginator(VRChecklist.objects.filter(qs_include).exclude(qs_exclude), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    page_details = {}
    page_details['first'] = paginator.page_range[0]
    page_details['last'] = paginator.page_range[len(paginator.page_range) - 1]
    return render_to_response('psc/vr_checklist_list.html', {'page_title': "Voter Registration Data Management", 'checklists': checklists, 'filter_form': filter_form, 'page_details' : page_details }, context_instance=RequestContext(request))

@login_required()
def dco_checklist_list(request):
    #qs = Q(date__in=[d[0] for d in DCO_DAYS if d[0]])
    qs_include = Q()
    if not request.session.has_key('dco_checklist_filter'):
        request.session['dco_checklist_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'state', 'first', 'second', 'day', 'observer_id']):
            request.session['dco_checklist_filter'] = request.GET
        filter_form = DCOChecklistFilterForm(request.session['dco_checklist_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['zone']:
                qs_include &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__parent__code__iexact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs_include &= Q(observer__location_id__in=LGA.objects.filter(parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['day']:
                qs_include &= Q(date=data['day'])

            if data['first'] == u'1':
                qs_include &= Q(submitted=True)
            elif data['first'] == u'2':
                qs_include &= Q(submitted=False)

            if data['second'] == u'1': # complete
                qs_include &= queries['dco']['status']['complete']
            elif data['second'] == u'2': # missing
                qs_include &= queries['dco']['status']['missing']
            elif data['second'] == u'3': # partial
                qs_include &= queries['dco']['status']['partial']
            elif data['second'] == u'4': # not open problem
                qs_include &= queries['dco']['status']['problem']
            elif data['second'] == u'5': # not open
                qs_include &= queries['dco']['status']['not_open']

            if data['observer_id']:
                qs_include = Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = DCOChecklistFilterForm()

    #get all objects
    global items_per_page
    if request.GET.get('export'):
	    items_per_page = DCOChecklist.objects.filter(qs_include).count()
    
    paginator = Paginator(DCOChecklist.objects.filter(qs_include).order_by('date', 'observer'), items_per_page)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # an invalid range will retrieve the last page of results
    try:
        checklists = paginator.page(page)
    except (EmptyPage, InvalidPage):
        checklists = paginator.page(paginator.num_pages)

    page_details = {}
    page_details['first'] = paginator.page_range[0]
    page_details['last'] = paginator.page_range[len(paginator.page_range) - 1]
    return render_to_response('psc/dco_checklist_list.html', {'page_title': "Display, Claims & Objections Data Management", 'checklists': checklists, 'filter_form': filter_form, 'page_details': page_details }, context_instance=RequestContext(request))

@login_required()
def vr_checklist(request, checklist_id=0):
    checklist = get_object_or_404(VRChecklist, pk=checklist_id)
    rcs = RegistrationCenter.objects.filter(parent=checklist.location.parent)
    location = checklist.observer.location
    if (request.POST):
        f = VRChecklistForm(request.POST, instance=checklist)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_checklist_list'))
    else:
        f = VRChecklistForm(instance=checklist)
        return render_to_response('psc/vr_checklist_form.html', {'page_title': "Voter Registration Checklist", 'checklist': checklist, 'rcs': rcs, 'location': location, 'form': f }, context_instance=RequestContext(request))

@login_required()
def dco_checklist(request, checklist_id=0):   
    checklist = get_object_or_404(DCOChecklist, pk=checklist_id)
    rcs = RegistrationCenter.objects.filter(parent=checklist.location.parent)
    location = checklist.observer.location
    if (request.POST):
        f = DCOChecklistForm(request.POST, instance=checklist)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.dco_checklist_list'))
    else:
        f = DCOChecklistForm(instance=checklist)
    return render_to_response('psc/dco_checklist_form.html', {'page_title': 'Display, Claims & Objections Checklist', 'checklist': checklist, 'rcs': rcs, 'location': location, 'form': f}, context_instance=RequestContext(request))

@login_required()
def vr_incident_update(request, incident_id=0):
    incident = get_object_or_404(VRIncident, pk=incident_id)
    #rc location for incident observer
    location = incident.observer.location
    lga_list = LGA.objects.all()
    rc_list_by_lga = RegistrationCenter.objects.filter(parent=incident.location.parent.id)
    
    if request.POST:        
        f = VRIncidentUpdateForm(request.POST, instance=incident)
        if f.is_valid():
            f.save()
        return HttpResponseRedirect(reverse('psc.views.vr_incident_list'))    
    else:
        f = VRIncidentForm(instance=incident)   
        return render_to_response('psc/vr_incident_update_form.html', {'page_title': "Voter Registration Critrical Incident", 'incident': incident, 'location': location, 'form': f, 'lga_list': lga_list, 'rc_list_by_lga': rc_list_by_lga }, context_instance=RequestContext(request))

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
    if not request.session.has_key('vr_incident_filter'):
        request.session['vr_incident_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'state', 'district', 'day', 'observer_id']):
            request.session['vr_incident_filter'] = request.GET
        filter_form = VRIncidentFilterForm(request.session['vr_incident_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data['zone']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__parent__parent__code__exact=data['zone']).values_list('id', flat=True))
            if data['state']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__parent__code__exact=data['state']).values_list('id', flat=True))
            if data['district']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__code__exact=data['district']).values_list('id', flat=True))
            if data['day']:
                qs &= Q(date=data['day'])
            if data['observer_id']:
                qs = Q(observer__observer_id__exact=data['observer_id'])
    else:
        filter_form = VRIncidentFilterForm()

    if request.GET.get('export'):
        global items_per_page
	items_per_page = VRIncident.objects.filter(qs).count()

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
    
    page_details = {}
    page_details['first'] = paginator.page_range[0]
    page_details['last'] = paginator.page_range[len(paginator.page_range) - 1]
    return render_to_response('psc/vr_incident_list.html', {'page_title': "Voter Registration Critical Incidents", 'checklists': checklists, 'filter_form': filter_form, 'page_details': page_details}, context_instance=RequestContext(request))

@login_required()
def dco_incident_list(request):
    qs = Q()
    if not request.session.has_key('dco_incident_filter'):
        request.session['dco_incident_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'state', 'district', 'day', 'observer_id']):
            request.session['dco_incident_filter'] = request.GET
        filter_form = DCOIncidentFilterForm(request.session['dco_incident_filter'])

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
                qs = Q(observer__observer_id__exact=data['observer_id'])
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

    page_details = {}
    page_details['first'] = paginator.page_range[0]
    page_details['last'] = paginator.page_range[len(paginator.page_range) - 1]
    return render_to_response('psc/dco_incident_list.html', {'page_title': "Display, Claims & Objections Critical Incidents", 'checklists': checklists, 'filter_form': filter_form, 'page_details': page_details}, context_instance=RequestContext(request))

@login_required()
def message_log(request):
    qs = Q()
    if not request.session.has_key('messagelog_filter'):
        request.session['messagelog_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['phone', 'message']):
            request.session['messagelog_filter'] = request.GET
        filter_form = MessagelogFilterForm(request.session['messagelog_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['phone']:
                qs &= Q(connection__identity__icontains=data['phone'].strip())
            if data['message']:
                qs &= Q(text__icontains=data['message'])
    else:
        filter_form = MessagelogFilterForm()
    
    messages = MessageTable(Message.objects.filter(qs), request=request)
    return render_to_response('psc/msg_log.html', { 'page_title': 'Message Log', 'messages_list' : messages, 'filter_form': filter_form }, context_instance=RequestContext(request))

@login_required()
@permission_required('psc.can_administer', login_url='/')
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
    return render_to_response('psc/action_log.html', {'page_title': 'Action Log', 'logs' : logs},  context_instance=RequestContext(request))

def ajax_fetch_rcs(request, method, lga_id=0):
    if lga_id:
        rcs = RegistrationCenter.objects.filter(parent__id=lga_id)

@login_required()
@permission_required('psc.can_analyse', login_url='/')
def export(request, model):
    import csv
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % model
    writer = csv.writer(response)

    def export_messagelog(writer):
        header =  ["Date","Phone","Direction","Text"]
        writer.writerow(header)
        
        messages = Message.objects.all().order_by('-date')        
        for message in messages:
            date = message.date.strftime('%Y-%m-%d %H:%M:%S')
            phone = message.connection.identity
            direction = message.direction
            text = message.text
            writer.writerow([date, phone, direction, text.replace('"', "'")])

    def export_vri(writer):
        header = ["PSC ID","Zone","State","LGA","VR","RC","A","B","C","D","E","F","G","H","J","K","M","N","P","Q","Comment"]
        writer.writerow(header)

        vris = VRIncident.objects.all()
        for vri in vris:
            pscid = vri.observer.observer_id
            lga = vri.location.parent.name
            if vri.location.parent.code == '999':
                if vri.observer.role == 'SDC':
                    zone = vri.observer.location.parent.parent.name
                    state = vri.observer.location.parent.name
                else:
                    zone = vri.observer.location.parent.name
                    state = vri.observer.location.name
            else:
                zone = vri.location.parent.parent.parent.parent.name
                state = vri.location.parent.parent.parent.name
            vr = vri.date.day
            rc = vri.location.code
            A = vri.A if vri.A else ""
            B = vri.B if vri.B else ""
            C = vri.C if vri.C else ""
            D = vri.D if vri.D else ""
            E = vri.E if vri.E else ""
            F = vri.F if vri.F else ""
            G = vri.G if vri.G else ""
            H = vri.H if vri.H else ""
            J = vri.J if vri.J else ""
            K = vri.K if vri.K else ""
            M = vri.M if vri.M else ""
            N = vri.N if vri.N else ""
            P = vri.P if vri.P else ""
            Q = vri.Q if vri.Q else ""
            comment = vri.comment if vri.comment else ""
            writer.writerow([pscid, zone, state, lga, vr, rc, A, B, C, D, E, F, G, H, J, K, M, N, P, Q, comment.replace('"', "'")])

    def export_dcoi(writer):
        header = ["PSC ID","Zone","State","LGA","DC","RC","A","B","C","D","E","F","G","H","J","K","Comment"]
        writer.writerow(header)

        dcois = DCOIncident.objects.all()
        for dcoi in dcois:
            pscid = dcoi.observer.observer_id
            lga = dcoi.location.parent.name
            if dcoi.location.parent.code == '999':
                if dcoi.observer.role == 'SDC':
                    zone = dcoi.observer.location.parent.parent.name
                    state = dcoi.observer.location.parent.name
                else:
                    zone = dcoi.observer.location.parent.name
                    state = dcoi.observer.location.name
            else:
                zone = dcoi.location.parent.parent.parent.parent.name
                state = dcoi.location.parent.parent.parent.name
            dc = dcoi.date.day
            rc = dcoi.location.code
            A = dcoi.A if dcoi.A else ""
            B = dcoi.B if dcoi.B else ""
            C = dcoi.C if dcoi.C else ""
            D = dcoi.D if dcoi.D else ""
            E = dcoi.E if dcoi.E else ""
            F = dcoi.F if dcoi.F else ""
            G = dcoi.G if dcoi.G else ""
            H = dcoi.H if dcoi.H else ""
            J = dcoi.J if dcoi.J else ""
            K = dcoi.K if dcoi.K else ""
            comment = dcoi.comment if dcoi.comment else ""
            writer.writerow([pscid, zone, state, lga, dc, rc, A, B, C, D, E, F, G, H, J, K, comment.replace('"', "'")])

    def export_vrc(writer):
        header =  ["PSC ID","Zone","State","LGA","VR","RC","A","B","C","D1","D2","D3","D4","E1","E2","E3","E4","E5","F","G","H","J","K","M","N","P","Q","R","S","T","U","V","W","X","Y","Z","AA","Comment"]
        writer.writerow(header)

        vrcs = VRChecklist.objects.filter(observer__role='LGA')
        for vrc in vrcs:
            pscid = vrc.observer.observer_id
            try:
                zone = vrc.location.parent.parent.parent.parent.name
                state = vrc.location.parent.parent.parent.name
                lga = vrc.location.parent.name
                rc = vrc.location.code
            except AttributeError:
                try:
                    zone = vrc.observer.location.parent.parent.parent.name
                    state = vrc.observer.location.parent.parent.name
                    lga = vrc.observer.location.name
                    rc = "999"
                except AttributeError:
                    zone = ""
                    state = ""
                    lga = "999"
                    rc = "999"
            vr = vrc.date.day
            A = vrc.A if vrc.A else ""
            B = vrc.B if vrc.B else ""
            C = vrc.C if vrc.C != None else ""
            D1 = "" if vrc.D1 == None else 1 if vrc.D1 == True else 2
            D2 = "" if vrc.D2 == None else 1 if vrc.D2 == True else 2
            D3 = "" if vrc.D3 == None else 1 if vrc.D3 == True else 2
            D4 = "" if vrc.D4 == None else 1 if vrc.D4 == True else 2
            E1 = "" if vrc.E1 == None else 1 if vrc.E1 == True else 2
            E2 = "" if vrc.E2 == None else 1 if vrc.E2 == True else 2
            E3 = "" if vrc.E3 == None else 1 if vrc.E3 == True else 2
            E4 = "" if vrc.E4 == None else 1 if vrc.E4 == True else 2
            E5 = "" if vrc.E5 == None else 1 if vrc.E5 == True else 2
            F = vrc.F if vrc.F != None else ""
            G = vrc.G if vrc.G else ""
            H = vrc.H if vrc.H else ""
            J = vrc.J if vrc.J else ""
            K = vrc.K if vrc.K else ""
            M = vrc.M if vrc.M else ""
            N = vrc.N if vrc.N else ""
            P = vrc.P if vrc.P else ""
            Q = vrc.Q if vrc.Q else ""
            R = vrc.R if vrc.R else ""
            S = vrc.S if vrc.S else ""
            T = vrc.T if vrc.T else ""
            U = vrc.U if vrc.U else ""
            V = vrc.V if vrc.V else ""
            W = vrc.W if vrc.W else ""
            X = vrc.X if vrc.X else ""
            Y = vrc.Y if vrc.Y != None else ""
            Z = vrc.Z if vrc.Z != None else ""
            AA = vrc.AA if vrc.AA != None else ""
            comment = vrc.comment
            writer.writerow([pscid, zone, state, lga, vr, rc, A, B, C, D1, D2, D3, D4, E1, E2, E3, E4, E5, F, G, H, J, K, M, N, P, Q, R, S, T, U, V, W, X, Y, Z, AA, comment.replace('"', "'")])

    def export_dcoc(writer):
        header =  ["PSC ID","Zone","State","LGA","DC","RC","A","B","C","D","E","F1","F2","F3","F4","F5","F6","F7","F8","F9","G","H","J","K","M","N","P","Q","R","S","T","U","V","W","X","Comment"]
        writer.writerow(header)

        dcocs = DCOChecklist.objects.filter(observer__role='LGA')
        for dcoc in dcocs:
            pscid = dcoc.observer.observer_id
            try:
                zone = dcoc.location.parent.parent.parent.parent.name
                state = dcoc.location.parent.parent.parent.name
                lga = dcoc.location.parent.name
                rc = dcoc.location.code
            except AttributeError:
                try:
                    zone = dcoc.observer.location.parent.parent.parent.name
                    state = dcoc.observer.location.parent.parent.name
                    lga = dcoc.observer.location.name
                    rc = "999"
                except AttributeError:
                    zone = ""
                    state = ""
                    lga = "999"
                    rc = "999"
            dc = dcoc.date.day
            A = dcoc.A if dcoc.A else ""
            B = dcoc.B if dcoc.B else ""
            C = dcoc.C if dcoc.C else ""
            D = dcoc.D if dcoc.D else ""
            E = dcoc.E if dcoc.E else ""
            F1 = "" if dcoc.F1 == None else 1 if dcoc.F1 == True else 2
            F2 = "" if dcoc.F2 == None else 1 if dcoc.F2 == True else 2
            F3 = "" if dcoc.F3 == None else 1 if dcoc.F3 == True else 2
            F4 = "" if dcoc.F4 == None else 1 if dcoc.F4 == True else 2
            F5 = "" if dcoc.F5 == None else 5 if dcoc.F5 == True else 2
            F6 = "" if dcoc.F6 == None else 1 if dcoc.F6 == True else 6
            F7 = "" if dcoc.F7 == None else 1 if dcoc.F7 == True else 2
            F8 = "" if dcoc.F8 == None else 1 if dcoc.F8 == True else 2
            F9 = "" if dcoc.F9 == None else 1 if dcoc.F9 == True else 2
            G = dcoc.G if dcoc.G else ""
            H = dcoc.H if dcoc.H else ""
            J = dcoc.J if dcoc.J else ""
            K = dcoc.K if dcoc.K else ""
            M = dcoc.M if dcoc.M else ""
            N = dcoc.N if dcoc.N else ""
            P = dcoc.P if dcoc.P else ""
            Q = dcoc.Q if dcoc.Q else ""
            R = dcoc.R if dcoc.R else ""
            S = dcoc.S if dcoc.S else ""
            T = dcoc.T if dcoc.T else ""
            U = dcoc.U if dcoc.U else ""
            V = dcoc.V if dcoc.V else ""
            W = dcoc.W if dcoc.W else ""
            X = dcoc.X if dcoc.X else ""
            comment = dcoc.comment
            writer.writerow([pscid, zone, state, lga, dc, rc, A, B, C, D, E, F1, F2, F3, F4, F5, F6, F7, F8, F9, G, H, J, K, M, N, P, Q, R, S, T, U, V, W, X, comment.replace('"', "'")])

    # export here
    # TODO: refactor
    export_method = eval("export_%s" % model)
    if hasattr(export_method, '__call__'):
        export_method(writer)
        return response

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def vr_zone_summary(request):
    filter_date = datetime.date(datetime.today())
    if not request.session.has_key('vr_zone_summary_filter'):
        request.session['vr_zone_summary_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['date']):
            request.session['vr_zone_summary_filter'] = request.GET
        filter_form = VRSummaryFilterForm(request.session['vr_zone_summary_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['date']:
                filter_date = datetime.date(datetime.strptime(data['date'], '%Y-%m-%d'))
    else:
        filter_form = VRSummaryFilterForm()
    q = Q(date=filter_date)

    ctx = RequestContext(request)
    ctx['page_title'] = 'Zone Summary'
    ctx['filter_form'] = filter_form
    ctx['zone_list'] = []
    zone_list = Zone.objects.all()

    for zone in zone_list:
        rcs_in_zone = RegistrationCenter.objects.filter(parent__parent__parent__parent__id=zone.pk).values_list('id', flat=True)
        qs = VRChecklist.objects.filter(q).filter(location_id__in=rcs_in_zone)
        zone_stats = {
            'name': zone.name,
            'n': qs.count(),
            'first_complete': qs.filter(queries['first']['complete']).count(),
            'first_missing': qs.filter(queries['first']['missing']).count(),
            'second_complete': qs.filter(queries['second']['complete']).count(),
            'second_missing': qs.filter(queries['second']['missing']).count(),
            'second_partial': qs.filter(queries['second']['partial']).count(),
            'second_problem': qs.filter(queries['second']['problem']).count(),
            'second_verified': qs.filter(queries['second']['verified']).count(),
            'third_complete': qs.filter(queries['third']['complete']).count(),
            'third_missing': qs.filter(queries['third']['missing']).count(),
            'third_partial': qs.filter(queries['third']['partial']).count(),
            'third_problem': qs.filter(queries['third']['problem']).count(),
            'third_verified': qs.filter(queries['third']['verified']).count(),
            'third_blank': qs.filter(queries['third']['blank']).count(),
        }
        ctx['zone_list'].append(zone_stats)
        
    return render_to_response('psc/vr_zone_summary.html', context_instance=ctx)

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def vr_state_summary(request):
    filter_date = datetime.date(datetime.today())
    if not request.session.has_key('vr_state_summary_filter'):
        request.session['vr_state_summary_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['date']):
            request.session['vr_state_summary_filter'] = request.GET
        filter_form = VRSummaryFilterForm(request.session['vr_state_summary_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['date']:
                filter_date = datetime.date(datetime.strptime(data['date'], '%Y-%m-%d'))
    else:
        filter_form = VRSummaryFilterForm()
    q = Q(date=filter_date)

    ctx = RequestContext(request)
    ctx['page_title'] = 'State Summary'
    ctx['filter_form'] = filter_form
    ctx['state_list'] = []
    state_list = State.objects.all().order_by('name')

    for state in state_list:
        rcs_in_state = RegistrationCenter.objects.filter(parent__parent__parent__id=state.pk).values_list('id', flat=True)
        qs = VRChecklist.objects.filter(q).filter(location_id__in=rcs_in_state)
        state_stats = {
            'name': state.name,
            'n': qs.count(),
            'first_complete': qs.filter(queries['first']['complete']).count(),
            'first_missing': qs.filter(queries['first']['missing']).count(),
            'second_complete': qs.filter(queries['second']['complete']).count(),
            'second_missing': qs.filter(queries['second']['missing']).count(),
            'second_partial': qs.filter(queries['second']['partial']).count(),
            'second_problem': qs.filter(queries['second']['problem']).count(),
            'second_verified': qs.filter(queries['second']['verified']).count(),
            'third_complete': qs.filter(queries['third']['complete']).count(),
            'third_missing': qs.filter(queries['third']['missing']).count(),
            'third_partial': qs.filter(queries['third']['partial']).count(),
            'third_problem': qs.filter(queries['third']['problem']).count(),
            'third_verified': qs.filter(queries['third']['verified']).count(),
            'third_blank': qs.filter(queries['third']['blank']).count(),
        }
        ctx['state_list'].append(state_stats)
        
    return render_to_response('psc/vr_state_summary.html', context_instance=ctx)

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def dco_zone_summary(request):
    filter_date = datetime.date(datetime.today())
    if not request.session.has_key('dco_zone_summary_filter'):
        request.session['dco_zone_summary_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['date']):
            request.session['dco_zone_summary_filter'] = request.GET
        filter_form = DCOSummaryFilterForm(request.session['dco_zone_summary_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['date']:
                filter_date = datetime.date(datetime.strptime(data['date'], '%Y-%m-%d'))
    else:
        filter_form = DCOSummaryFilterForm()
    q = Q(date=filter_date)

    ctx = RequestContext(request)
    ctx['page_title'] = 'Zone Summary'
    ctx['filter_form'] = filter_form
    ctx['zone_list'] = []
    zone_list = Zone.objects.all()

    for zone in zone_list:
        rcs_in_zone = RegistrationCenter.objects.filter(parent__parent__parent__parent__id=zone.pk).values_list('id', flat=True)
        qs = DCOChecklist.objects.filter(q).filter(location_id__in=rcs_in_zone)
        zone_stats = {
            'name': zone.name,
            'n': qs.count(),
            'arrived_yes': qs.filter(queries['dco']['arrival']['yes']).count(),
            'arrived_no': qs.filter(queries['dco']['arrival']['no']).count(),
            'status_complete': qs.filter(queries['dco']['status']['complete']).count(),
            'status_missing': qs.filter(queries['dco']['status']['missing']).count(),
            'status_partial': qs.filter(queries['dco']['status']['partial']).count(),
            'status_problem': qs.filter(queries['dco']['status']['problem']).count(),
            'status_not_open': qs.filter(queries['dco']['status']['not_open']).count(),
        }
        ctx['zone_list'].append(zone_stats)
        
    return render_to_response('psc/dco_zone_summary.html', context_instance=ctx)

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def dco_state_summary(request):
    filter_date = datetime.date(datetime.today())
    if not request.session.has_key('dco_state_summary_filter'):
        request.session['dco_state_summary_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['date']):
            request.session['dco_state_summary_filter'] = request.GET
        filter_form = DCOSummaryFilterForm(request.session['dco_state_summary_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['date']:
                filter_date = datetime.date(datetime.strptime(data['date'], '%Y-%m-%d'))
    else:
        filter_form = DCOSummaryFilterForm()
    q = Q(date=filter_date)

    ctx = RequestContext(request)
    ctx['page_title'] = 'State Summary'
    ctx['filter_form'] = filter_form
    ctx['state_list'] = []
    state_list = State.objects.all().order_by('name')

    for state in state_list:
        rcs_in_state = RegistrationCenter.objects.filter(parent__parent__parent__id=state.pk).values_list('id', flat=True)
        qs = DCOChecklist.objects.filter(q).filter(location_id__in=rcs_in_state)
        state_stats = {
            'name': state.name,
            'n': qs.count(),
            'arrived_yes': qs.filter(queries['dco']['arrival']['yes']).count(),
            'arrived_no': qs.filter(queries['dco']['arrival']['no']).count(),
            'status_complete': qs.filter(queries['dco']['status']['complete']).count(),
            'status_missing': qs.filter(queries['dco']['status']['missing']).count(),
            'status_partial': qs.filter(queries['dco']['status']['partial']).count(),
            'status_problem': qs.filter(queries['dco']['status']['problem']).count(),
            'status_not_open': qs.filter(queries['dco']['status']['not_open']).count(),
        }
        ctx['state_list'].append(state_stats)
        
    return render_to_response('psc/dco_state_summary.html', context_instance=ctx)

def vr_checklist_analysis(request):
    vr_days = [day[0] for day in VR_DAYS if day[0]]

    qs = Q(submitted=True)
    qs &= Q(date__in=vr_days)

    if not request.session.has_key('vr_analysis_filter'):
        request.session['vr_analysis_filter'] = {}

    if request.method == 'GET':
        if filter(lambda key: request.GET.has_key(key), ['zone', 'state', 'date']):
            request.session['vr_analysis_filter'] = request.GET
        filter_form = VRAnalysisFilterForm(request.session['vr_analysis_filter'])

        if filter_form.is_valid():
            data = filter_form.cleaned_data

            if data['state']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__parent__code__iexact=data['state']).values_list('id', flat=True))
            elif data['zone']:
                qs &= Q(location_id__in=RegistrationCenter.objects.filter(parent__parent__parent__parent__code__iexact=data['zone']).values('id'))
            if data['date']:
                qs &= Q(date=datetime.date(datetime.strptime(data['date'], '%Y-%m-%d')))
    else:
        filter_form = VRAnalysisFilterForm()

    ctx = RequestContext(request)
    ctx['question'] = dict()
    ctx['question']['no_of_checklists'] = stats.vr_N(qs)
    ctx['question']['A'] = stats.vr_QA(qs)

    #for B through AA
    qs &= ~Q(A=4)
    ctx['question']['B'] = stats.vr_QB(qs)
    ctx['question']['C'] = stats.vr_QC(qs)
    ctx['question']['D'] = stats.vr_QD(qs)
    ctx['question']['E'] = stats.vr_QE(qs)
    ctx['question']['F'] = stats.vr_QF(qs)
    ctx['question']['G'] = stats.vr_QG(qs)
    ctx['question']['H'] = stats.vr_QH(qs)
    ctx['question']['J'] = stats.vr_QJ(qs)
    ctx['question']['K'] = stats.vr_QK(qs)
    ctx['question']['M'] = stats.vr_QM(qs)
    ctx['question']['N'] = stats.vr_QN(qs)
    ctx['question']['P'] = stats.vr_QP(qs)
    ctx['question']['Q'] = stats.vr_QQ(qs)
    ctx['question']['R'] = stats.vr_QR(qs)
    ctx['question']['S'] = stats.vr_QS(qs)
    ctx['question']['T'] = stats.vr_QT(qs)
    ctx['question']['U'] = stats.vr_QU(qs)
    ctx['question']['V'] = stats.vr_QV(qs)
    ctx['question']['W'] = stats.vr_QW(qs)
    ctx['question']['X'] = stats.vr_QX(qs)
    ctx['question']['Y'] = stats.vr_QY(qs)
    ctx['question']['Z'] = stats.vr_QZ(qs)
    ctx['question']['AA'] = stats.vr_QAA(qs)

    return render_to_response('psc/vr_checklist_analysis.html', {'page_title': 'Voter Registration Checklist Analysis', 'filter_form': filter_form}, context_instance=ctx)


#ajax methods
def get_rcs_by_lga(request, lga_id=0):
    if lga_id:
        rcs = serializers.serialize('json', RegistrationCenter.objects.filter(parent=lga_id))
        return HttpResponse(mimetype='application/json', content=rcs)

def get_states_by_zone(request, zone):
    if zone:
        states = serializers.serialize('json', State.objects.filter(parent__code=zone))
        return HttpResponse(mimetype='application/jsoin', content=states)

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def vr_incident_delete(request, incident_id):
    if int(incident_id):        
        VRIncident.objects.get(pk=incident_id).delete()
        return HttpResponseRedirect(reverse('psc.views.vr_incident_list'))

@permission_required('psc.can_analyse', login_url='/')
@login_required()
def dco_incident_delete(request, incident_id):
    if int(incident_id):        
        DCOIncident.objects.get(pk=incident_id).delete()
        return HttpResponseRedirect(reverse('psc.views.dco_incident_list'))

#@permission_required('psc.can_analyse', login_url='/')
#@login_required()
def send_mail(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipients = []
        #if to single person
        if request.POST.get('psc_id', 0):
            psc_id = int(request.POST.get('psc_id'))
            email = Observer.objects.get(observer_id=psc_id).email
            recipients.append(email)
            
        #if to multiple recipients
        if request.POST.getlist('recipient'):
            roles = request.POST.getlist('recipient')
            email_list = Observer.objects.filter(role__in=roles).values_list('email', flat=True)
            recipients.extend(email_list)

        #confirm = send_mail(subject, message, 'admin@psc2011.co.cc', recipients, fail_silently=False)
        return HttpResponseRedirect(reverse('psc.views.send_mail'))
    else:
        form = EmailBlastForm()
        return render_to_response('psc/send_mail.html', { 'form': form }, context_instance=RequestContext(request))
