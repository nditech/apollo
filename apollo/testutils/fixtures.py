# -*- coding: utf-8 -*-
from apollo import models
from apollo.core import db


def create_deployment(name):
    deployment = models.Deployment(name=name, hostnames=['localhost'])

    db.session.add(deployment)
    db.session.commit()

    return deployment


def create_event(deployment_id, name, start, end):
    event = models.Event(
        deployment_id=deployment_id, name=name, start=start, end=end)

    db.session.add(event)
    db.session.commit()

    return event


def create_form_set(deployment_id, name):
    form_set = models.FormSet(deployment_id=deployment_id, name=name)

    db.session.add(form_set)
    db.session.commit()

    return form_set


def _create_form(deployment_id, form_set_id, name, prefix, form_type):
    form = models.Form(
        deployment_id=deployment_id, form_set_id=form_set_id,
        name=name, prefix=prefix, form_type=form_type)

    db.session.add(form)
    db.session.commit()

    return form


def create_checklist_form(deployment_id, form_set_id, name, prefix):
    return _create_form(deployment_id, form_set_id, name, prefix, 'CHECKLIST')


def create_incident_form(deployment_id, form_set_id, name, prefix):
    return _create_form(deployment_id, form_set_id, name, prefix, 'INCIDENT')


def create_participant_set(deployment_id, name):
    participant_set = models.ParticipantSet(
        deployment_id=deployment_id, name=name)

    db.session.add(participant_set)
    db.session.commit()

    return participant_set
