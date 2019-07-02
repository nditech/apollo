# -*- coding: utf-8 -*-
from flask import Blueprint

from apollo.deployments.api import views

blueprint = Blueprint('deployments', __name__)

blueprint.add_url_rule(
    '/api/events/<int:event_id>',
    view_func=views.EventItemResource.as_view('api_event_item'))
blueprint.add_url_rule(
    '/api/events',
    view_func=views.EventListResource.as_view('api_event_list'))
