# -*- coding: utf-8 -*-
import logging
import pathlib
import warnings

from sqlalchemy.sql import text

from apollo import models
from apollo.core import db

logger = logging.getLogger(__name__)


def load_sql_fixture(fixture):
    source_file = pathlib.Path(fixture)
    if source_file.exists() and source_file.is_file():
        query_text = text(source_file.read_text())
        try:
            db.engine.execute(query_text)
        except Exception as ex:
            logger.exception('Error occurred executing fixture statement(s)')
    else:
        warnings.warn(f'Invalid fixture specified: {source_file}')


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
