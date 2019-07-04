# -*- coding: utf-8 -*-
from flask import Blueprint

from apollo.core import docs
from apollo.deployments.api import views

blueprint = Blueprint('deployments', __name__)

blueprint.add_url_rule(
    '/api/events/<int:event_id>',
    view_func=views.EventItemResource.as_view('api_event_item'))
blueprint.add_url_rule(
    '/api/events',
    view_func=views.EventListResource.as_view('api_event_list'))

docs.register(views.EventItemResource, 'deployments.api_event_item')
docs.register(views.EventListResource, 'deployments.api_event_list')