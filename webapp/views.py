# Create your views here.
from django.shortcuts import render_to_response
from djangomako.shortcuts import render_to_string

def home(request):
    return render_to_response('webapp/index.html')

def test(request):
    return render_to_response('webapp/index2.html')

def app_templates():
    return render_to_string('webapp/templates.html', {})