from . import route
from ..messaging.forms import KannelForm, TelerivetForm
from ..messaging.helpers import parse_message
from flask import Blueprint, make_response, request
import json


bp = Blueprint('messaging', __name__)


@route(bp, '/messaging/kannel', methods=['GET'])
def kannel_view():
    form = KannelForm(request.args)
    if form.validate():
        response = parse_message(form)
        return response
    print form.errors
    return ""


@route(bp, '/messaging/telerivet', methods=['POST'])
def telerivet_view(request):
    form = TelerivetForm(request.POST)
    if form.validdate():
        response_text = parse_message(form)
        response = {'messages': [{'content': response_text}]}
        http_response = make_response(json.dumps(response))
        http_response.headers['Content-Type'] = 'application/json'
        return http_response
    return ""
