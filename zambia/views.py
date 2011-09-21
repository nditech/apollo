# Create your views here.
from django.http import HttpResponse
from webapp.models import *
from models import *
from api import *
from queries import checklist_status
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from djangomako.shortcuts import render_to_string
import json
from xlwt import *
from datetime import datetime
from stats import *

@login_required
def dashboard_stats(request):
    province = request.GET.get('province', None)
    district = request.GET.get('district', None)
    polling_district = request.GET.get('polling_district', None)
    polling_stream = request.GET.get('polling_stream', None)
    sample = request.GET.get('sample', None)
    
    # checklist statistics
    checklist_filter = {}
    
    if polling_stream:
        try:
            checklist_filter['location__id'] = int(polling_stream)
        except ValueError:
            pass
    elif polling_district:
        try:
            checklist_filter['location__parent__parent__id'] = int(polling_district)
        except ValueError:
            pass
    elif district:
        try:
            checklist_filter['location__parent__parent__parent__parent__parent__id'] = int(district)
        except ValueError:
            pass
    elif province:
        try:
            checklist_filter['location__parent__parent__parent__parent__parent__parent__id'] = int(province)
        except ValueError:
            pass
    if sample:
        checklist_filter['location__pk__in'] = Sample.objects.filter(sample=sample).values_list('location__pk', flat=True)
    
    dashboard_checklist_status = {
        'setup_complete': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['setup_complete']).count(),
        'setup_missing': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['setup_missing']).count(),
        'setup_partial': Checklist.objects.filter(**checklist_filter).filter(checklist_status['setup_partial']).count(),
        
        'voting_complete': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['voting_complete']).count(),
        'voting_missing': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['voting_missing']).count(),
        'voting_partial': Checklist.objects.filter(**checklist_filter).filter(checklist_status['voting_partial']).count(),
        
        'closing_complete': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['closing_complete']).count(),
        'closing_missing': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['closing_missing']).count(),
        'closing_partial': Checklist.objects.filter(**checklist_filter).filter(checklist_status['closing_partial']).count(),
        
        'counting_complete': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['counting_complete']).count(),
        'counting_missing': Checklist.objects.filter(**checklist_filter).filter(**checklist_status['counting_missing']).count(),
        'counting_partial': Checklist.objects.filter(**checklist_filter).filter(checklist_status['counting_partial']).count(),
    }
         
    return HttpResponse(json.dumps(dashboard_checklist_status), mimetype="application/json")

@login_required
@permission_required('webapp.can_export')
def export_checklists(request):
    request_params = request.GET
    resource = ChecklistsResource()
    
    applicable_filters = resource.build_filters(request_params)
    obj_list = list(resource.apply_filters(request, applicable_filters))
    
    wb = Workbook()
    ws = wb.add_sheet('Checklists');
    
    # write row header
    columns = ['PDID', 'Monitor Id', 'Monitor Name', 'Monitor Phone', 'Supervisor Name', 'Supervisor Phone', 'Time', 'Province', 'District', 'Constituency', 'Ward', 
        'Polling District', 'Polling Station', 'Polling Stream',
        '1', '2', '3a', '3b', '3c', '3d', '3e', '3f', '3g', '3h', '4', '5', '5a',
        '5b', '5c', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
        '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', 
        '28a1', '28a2', '28b1', '28b2', '28c1', '28c2', '28d1', '28d2', '28e1', '28e2',
        '29a1', '29b1', '29c1', '29d1', '29e1', '29f1', '29g1', '29h1', '29i1', '29j1', '29k1', '29l1', 
        '29a2', '29b2', '29c2', '29d2', '29e2', '29f2', '29g2', '29h2', '29i2', '29j2', '29k2', '29l2',  
        '30', '31', '32', '33']
    
    data_fields = ['location.parent.code', 'observer.observer_id', 'observer.name', 'observer.connection_set.all()[0].identity', 'observer.supervisor.name', 'observer.supervisor.connection_set.all()[0].identity', 
        'response.updated', 'location.parent.parent.parent.parent.parent.parent.name', 
        'location.parent.parent.parent.parent.parent.name', 'location.parent.parent.parent.parent.name', 
        'location.parent.parent.parent.name', 
        'location.parent.parent.name', 'location.parent.name', 'location.name',
        'response.A', 'response.B', 'response.CA', 'response.CB', 'response.CC', 'response.CD', 'response.CE', 
        'response.CF', 'response.CG', 'response.CH', 'response.D', 'response.E', 'response.EA',
        'response.EB', 'response.EC', 'response.F', 'response.G', 'response.H', 'response.J', 'response.K',
        'response.M', 'response.N', 'response.P', 'response.Q', 'response.R', 'response.S',
        'response.T', 'response.U', 'response.V', 'response.W', 'response.X', 'response.Y', 'response.Z', 
        'response.AA', 'response.AB', 'response.AC', 'response.AD', 
        'response.AEAA', 'response.AEAB', 'response.AEBA', 'response.AEBB', 'response.AECA', 'response.AECB', 
        'response.AEDA', 'response.AEDB', 'response.AEEA', 'response.AEEB',
        'response.AGA', 'response.AHA', 'response.AJA', 'response.AKA', 'response.AMA', 'response.ANA', 'response.APA', 'response.AQA', 'response.ARA', 'response.ASA', 'response.ATA', 'response.AUA', 
        'response.AGB', 'response.AHB', 'response.AJB', 'response.AKB', 'response.AMB', 'response.ANB', 'response.APB', 'response.AQB', 'response.ARB', 'response.ASB', 'response.ATB', 'response.AUB',  
        'response.AV', 'response.AW', 'response.AX', 'response.AY']
    
    for i, column in enumerate(columns):
        ws.write(0, i, column)

    for row, checklist in enumerate(obj_list):
        for j, field in enumerate(data_fields):
            exec 'value = checklist.%s' % field
            ws.write(row+1, j, unicode(value))
    
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=checklist_export-%d%02d%02d-%02d%02d.xls' % \
        (datetime.today().year, datetime.today().month, datetime.today().day, datetime.today().hour, datetime.today().minute)

    wb.save(response)
    return response

@login_required
@permission_required('webapp.can_export')
def export_incidents(request):
    request_params = request.GET
    resource = IncidentsResource()
    
    applicable_filters = resource.build_filters(request_params)
    obj_list = list(resource.apply_filters(request, applicable_filters))
    
    wb = Workbook()
    ws = wb.add_sheet('Incidents');
    
    if settings.ZAMBIA_DEPLOYMENT == 'RRP':
        # write row header
        columns = ['PDID', 'Monitor Id', 'Time', 'Province', 'District', 'Constituency', 'Ward', 
            'Polling District', 'Polling Station', 'Polling Stream',
            '1', '2a', '2b', '2c', '2d', '2e', '2f', '2g', '2h', '2i', '2j', '2k',
            '2k1', '2k2', '2k4', '2l', '2m', '2n', '2o', '3']
    
        data_fields = ['location.parent.code', 'observer.observer_id', 'response.updated', 'location.parent.parent.parent.parent.parent.parent.name', 
            'location.parent.parent.parent.parent.parent.name', 'location.parent.parent.parent.parent.name', 
            'location.parent.parent.parent.name', 
            'location.parent.parent.name', 'location.parent.name', 'location.name',
            'response.W', 'response.A', 'response.B', 'response.C', 'response.D', 'response.E', 'response.F', 
            'response.G', 'response.H', 'response.I', 'response.J', 'response.K', 'response.K1',
            'response.K2', 'response.K4', 'response.L', 'response.M', 'response.N', 'response.O', 'response.description']
    else:
        # write row header
        columns = ['PDID', 'Monitor Name', 'Monitor Phone', 'Time', 'Province', 'District', 'Constituency', 'Ward', 
            'Polling District', 'Polling Station', 'Polling Stream',
            '1', '2a', '2b', '2c', '2d', '2e', '2f', '2g', '2h', '2i', '2j', '2k',
            '2k1', '2k2', '2k4', '2l', '2m', '2n', '2o', '3']
    
        data_fields = ['location.parent.code', 'response.monitor_name', 'response.monitor_phone', 'updated', 'location.parent.parent.parent.parent.parent.parent.name', 
            'location.parent.parent.parent.parent.parent.name', 'location.parent.parent.parent.parent.name', 
            'location.parent.parent.parent.name', 
            'location.parent.parent.name', 'location.parent.name', 'location.name',
            'response.W', 'response.A', 'response.B', 'response.C', 'response.D', 'response.E', 'response.F', 
            'response.G', 'response.H', 'response.I', 'response.J', 'response.K', 'response.K1',
            'response.K2', 'response.K4', 'response.L', 'response.M', 'response.N', 'response.O', 'response.description']
    
    for i, column in enumerate(columns):
        ws.write(0, i, column)

    for row, incident in enumerate(obj_list):
        for j, field in enumerate(data_fields):
            exec 'value = incident.%s' % field
            ws.write(row+1, j, str(value))
    
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=incident_export-%d%02d%02d-%02d%02d.xls' % \
        (datetime.today().year, datetime.today().month, datetime.today().day, datetime.today().hour, datetime.today().minute)

    wb.save(response)
    return response

@login_required
@permission_required('webapp.can_analyse')
def process_analysis(request):
    if request.POST:
        request_params = request.POST.copy()
        sample = request.POST.get('sample', None)
    else:
        request_params = {}
        sample = None
    
    context = {'title': 'Elections Process Analysis'}
    # remove empty parameters
    for key in request_params.keys():
        if not request_params.get(key):
            del request_params[key]
        
    resource = ChecklistsResource()
    applicable_filters = resource.build_filters(request_params)
            
    if sample:
        if applicable_filters.has_key('location__id__in'):
            applicable_filters['location__id__in'] = [int(id) for id in list(set(Sample.objects.filter(sample=sample).values_list('location__pk', flat=True)) & set(applicable_filters['location__id__in']))]
        else:
            applicable_filters['location__id__in'] = [int(id) for id in Sample.objects.filter(sample=sample).values_list('location__pk', flat=True)]
    
    # remove empty attributes
    for key in applicable_filters.keys():
        if applicable_filters.get(key) == []:
            del applicable_filters[key]
        
    query = ",".join(['%s=%s' % (key, applicable_filters[key]) for key in applicable_filters.keys()])
    
    if query:
        exec 'q = Q(%s)' % query
    else:
        q = Q()
    
    location_id = request.POST.get('location__id', None)
    if location_id:
        context['location'] = Location.objects.get(pk=location_id)
    else:
        context['location'] = Location.objects.get(name="Zambia",type__name="Country")
        
    context['total'] = checklist_N(q)
    
    context['A'] = checklist_Q_options('A', q)
    context['B'] = checklist_Q_options('B', q)
    context['CA'] = checklist_Q_options('CA', q)
    context['CB'] = checklist_Q_options('CB', q)
    context['CC'] = checklist_Q_options('CC', q)
    context['CD'] = checklist_Q_options('CD', q)
    context['CE'] = checklist_Q_options('CE', q)
    context['CF'] = checklist_Q_options('CF', q)
    context['CG'] = checklist_Q_options('CG', q)
    context['CH'] = checklist_Q_options('CH', q)
    context['EA'] = checklist_Q_options('EA', q)
    context['EB'] = checklist_Q_options('EB', q)
    context['EC'] = checklist_Q_options('EC', q)
    context['F'] = checklist_Q_options('F', q)
    context['G'] = checklist_Q_options('G', q)
    context['K'] = checklist_Q_options('K', q)
    context['M'] = checklist_Q_options('M', q)
    context['N'] = checklist_Q_options('N', q)
    context['P'] = checklist_Q_options('P', q)
    context['Q'] = checklist_Q_options('Q', q)
    context['R'] = checklist_Q_options('R', q)
    context['S'] = checklist_Q_options('S', q)
    context['T'] = checklist_Q_options('T', q)
    context['U'] = checklist_Q_options('U', q)
    context['V'] = checklist_Q_options('V', q)
    context['W'] = checklist_Q_options('W', q)
    context['X'] = checklist_Q_options('X', q)
    context['Y'] = checklist_Q_options('Y', q)
    context['Z'] = checklist_Q_options('Z', q)
    context['AA'] = checklist_Q_options('AA', q)
    context['AB'] = checklist_Q_options('AB', q)
    context['AC'] = checklist_Q_options('AC', q)
    context['AD'] = checklist_Q_options('AD', q)
    context['AV'] = checklist_Q_options('AV', q)
    context['AW'] = checklist_Q_options('AW', q)
    context['AX'] = checklist_Q_options('AX', q)
    context['AY'] = checklist_Q_options('AY', q)
    
    context['D'] = checklist_Q_mean('D', q)
    context['E'] = checklist_Q_mean('E', q)
    context['H'] = checklist_Q_mean('H', q)
        
    return render_to_response('zambia/process_analysis.html', RequestContext(request, context))

@login_required
@permission_required('webapp.can_analyse')
def results_analysis(request):
    context = {'title': 'Elections Results Analysis'}
    return render_to_response('zambia/results_analysis.html', RequestContext(request, context))
    
def app_templates(context):
    return render_to_string('zambia/templates.html', {}, context)