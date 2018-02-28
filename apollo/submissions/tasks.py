# -*- coding: utf-8 -*-
from apollo import models
from apollo.factory import create_celery_app

celery = create_celery_app()


@celery.task
def init_submissions(event_id, form_id, role_id, location_type_id):
    event = models.Event.query.filter_by(id=event_id).first()
    form = models.Form.query.filter_by(id=form_id).first()
    role = models.ParticipantRole.query.filter_by(id=role_id).first()
    location_type = models.LocationType.query.filter_by(
        id=location_type_id).first()

    if not (event and form and role and location_type):
        return

    models.Submission.init_submissions(event, form, role, location_type)
