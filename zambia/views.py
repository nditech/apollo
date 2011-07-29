# Create your views here.
from djangomako.shortcuts import render_to_string

def app_templates():
    return render_to_string('zambia/templates.html', {})