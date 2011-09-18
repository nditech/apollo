# Create your views here.
from django.http import HttpResponse
from webapp.models import *
from queries import checklist_status
from djangomako.shortcuts import render_to_string
import json

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
        pass
    
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
    
def app_templates(context):
    return render_to_string('zambia/templates.html', {}, context)