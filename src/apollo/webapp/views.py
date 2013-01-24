# Create your views here.
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from djangomako.shortcuts import render_to_string
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext
from django.http import *
from django.conf import settings
from api import *
from tasks import *
from zambia.api import *
import re

@login_required
def home(request):
    return render_to_response('webapp/index.html', {'context_instance': RequestContext(request, {'settings': settings})})

def test(request):
    return render_to_response('webapp/index2.html')

def app_templates(context):
    return render_to_string('webapp/templates.html', {}, context)

@permission_required('webapp.can_sms')
@csrf_exempt
def send_sms(request):    
    if request.POST:
        collection_type = request.POST.get('collection_type', '')
        message = request.POST.get('message', '')
        
        if collection_type == 'contact':
            resource = ContactResource()
        elif collection_type == 'incident':
            resource = IncidentsResource()
        elif collection_type == 'checklist':
            resource = ChecklistsResource()
        
        request_params = request.POST
        applicable_filters = resource.build_filters(request_params)
        obj_list = resource.apply_filters(request, applicable_filters)
        
        if collection_type == 'contact':
            phone_numbers = [re.sub(r'^0', '260', contact.connection_set.all()[0].identity).replace(" ", "") for contact in obj_list if contact.connection_set.all()[0].identity]
        elif collection_type == 'incident':
            phone_numbers = [re.sub(r'^0', '260', incident.observer.connection_set.all()[0].identity).replace(" ", "") for incident in obj_list if incident.observer.connection_set.all()[0].identity]
        elif collection_type == 'checklist':
            phone_numbers = [re.sub(r'^0', '260', checklist.observer.connection_set.all()[0].identity).replace(" ", "") for checklist in obj_list if checklist.observer.connection_set.all()[0].identity]
        
        phone_numbers += settings.PHONE_CC
        
        to = ",".join(set(phone_numbers))
        if to:
            MessageBlast.delay(to, message)
            return HttpResponse(len(phone_numbers))
        else:
            return HttpResponseBadRequest()
            
    return HttpResponseBadRequest()