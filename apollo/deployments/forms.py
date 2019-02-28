# -*- coding: utf-8 -*-
from flask import g
from flask_babelex import lazy_gettext as _
from flask_security import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, fields, validators

from apollo import services
from apollo.deployments.models import Event
from apollo.locations.models import LocationSet
from apollo.participants.models import ParticipantSet


def generate_event_selection_form(*args, **kwargs):
    # restrict choices to events they have permission to access
    if current_user.is_anonymous:
        choices = []
    else:
        user = current_user._get_current_object()
        if user.is_admin():
            query = Event.query.filter_by(
                deployment_id=user.deployment_id)
        else:
            perm_cache = services.users.get_permissions_cache(user)
            allowed_event_ids = [
                n.value for n in perm_cache
                if n.method == 'access_resource' and n.type == 'event']
            query = Event.query.filter(
                Event.resource_id.in_(allowed_event_ids),
                Event.deployment_id == user.deployment_id)

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


class DeploymentForm(FlaskForm):
    name = fields.StringField(
        _('Name'), validators=[validators.DataRequired()])
    hostnames = fields.TextAreaField(
        _('Hostnames'), validators=[validators.DataRequired()])
    allow_observer_submission_edit = fields.BooleanField(
        _('Allow editing of observer submissions'))
    logo = fields.FileField()
    include_rejected_in_votes = fields.BooleanField()


def event_form_factory(*args, **kwargs):
    form_choices = Form.query.with_entities(Form.id, Form.name).all()
    location_set_choices = LocationSet.query.with_entities(
        LocationSet.id, LocationSet.name).all()
    participant_set_choices = ParticipantSet.query.with_entities(
        ParticipantSet.id, ParticipantSet.name).all()

    class EventForm(FlaskForm):
        start = fields.DateTimeField(
            _('Start'), validators=[validators.DataRequired()])
        end = fields.DateTimeField(
            _('End'), validators=[validators.DataRequired()])
        forms = fields.SelectMultipleField(_('Forms'), choices=form_choices)
        location_set = fields.SelectField(
            _('Location set'), choices=location_set_choices)
        participant_set = fields.SelectField(
            _('Participant set'), choices=participant_set_choices)

    return EventForm(*args, **kwargs)


class SetForm(FlaskForm):
    name = fields.StringField(
        _('Name'), validators=[validators.DataRequired()])
