# Create your views here.
from django.shortcuts import render_to_response
from djangomako.shortcuts import render_to_string
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext
from django.conf import settings

@login_required
def home(request):
    return render_to_response('webapp/index.html', {'context_instance': RequestContext(request, {'settings': settings})})

def test(request):
    return render_to_response('webapp/index2.html')

def app_templates(context):
    return render_to_string('webapp/templates.html', {}, context)

def send_sms(request):
    pass