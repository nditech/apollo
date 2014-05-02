from . import route
from .. import services
from ..messaging.forms import KannelForm, TelerivetForm
from ..messaging.helpers import parse_message
from flask import Blueprint, make_response, request, g
import json


bp = Blueprint('messaging', __name__)


@route(bp, '/messaging/kannel', methods=['GET'])
def kannel_view():
    form = KannelForm(request.args)
    if form.validate():
        msg = form.get_message()
        services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN')

        response = parse_message(form)

        services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response,
            direction='OUT')
        return response
    print form.errors
    return ""


@route(bp, '/messaging/telerivet', methods=['POST'])
def telerivet_view(request):
    form = TelerivetForm(request.POST)
    if form.validdate():
        msg = form.get_message()
        services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN')

        response_text = parse_message(form)
        response = {'messages': [{'content': response_text}]}
        http_response = make_response(json.dumps(response))
        http_response.headers['Content-Type'] = 'application/json'

        services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response_text,
            direction='OUT')
        return http_response
    return ""
