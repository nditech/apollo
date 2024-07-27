# -*- coding: utf-8 -*-
from flask import g
from flask_babelex import gettext as _
from flask_security import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, validators

from apollo import services
from apollo.deployments.models import Event


def generate_event_selection_form(*args, **kwargs):
    # restrict choices to events they have permission to access
    if current_user.is_anonymous:
        choices = []
    else:
        user = current_user._get_current_object()
        query = Event.query.filter(
            Event.deployment_id == user.deployment_id,
            Event.is_hidden == False, # noqa
        )
        if not user.is_admin():
            perm_cache = services.users.get_permissions_cache(user)
            allowed_event_ids = [
                n.value for n in perm_cache
                if n.method == 'access_resource' and n.type == 'event']
            query = query.filter(Event.resource_id.in_(allowed_event_ids))

        choices = [
            (e.id, e.name) for e in query.with_entities(
                Event.id, Event.name).order_by(Event.start.desc())]

    class EventSelectionForm(FlaskForm):
        event = SelectField(
            _('Choose Event'),
            choices=choices,
            coerce=int,
            default=g.event.id,
            validators=[validators.input_required()]
        )

    return EventSelectionForm(*args, **kwargs)
