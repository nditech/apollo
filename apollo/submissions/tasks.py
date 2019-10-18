# -*- coding: utf-8 -*-
import logging
import os

from apollo import models, helpers
from apollo.core import uploads
from apollo.factory import create_celery_app
from apollo.participants.models import Participant
from flask_babelex import gettext
from ..models import Submission
from ..users.models import UserUpload

celery = create_celery_app()
logger = logging.getLogger(__name__)


@celery.task(bind=True)
def init_submissions(
        self, event_id, form_id, role_id, location_type_id, channel=None):
    event = models.Event.query.filter_by(id=event_id).first()
    form = models.Form.query.filter_by(id=form_id).first()
    role = models.ParticipantRole.query.filter_by(id=role_id).first()
    location_type = models.LocationType.query.filter_by(
        id=location_type_id).first()

    if not (event and form and role and location_type):
        return

    models.Submission.init_submissions(event, form, role, location_type, self)


@celery.task(bind=True)
def init_survey_submissions(self, event_id, form_id, upload_id):
    event = models.Event.query.filter_by(id=event_id).first()
    form = models.Form.query.filter_by(id=form_id).first()

    upload = UserUpload.query.filter(UserUpload.id == upload_id).first()
    if not upload:
        logger.error('Upload %s does not exist, aborting', upload_id)
        return

    filepath = uploads.path(upload.upload_filename)

    if not os.path.exists(filepath):
        logger.error('Upload file %s does not exist, aborting', filepath)
        upload.delete()
        return

    with open(filepath, 'rb') as f:
        dataframe = helpers.load_source_file(f)

        total_records = dataframe.shape[0]
        processed_records = 0
        error_records = 0
        warning_records = 0
        error_log = []

        for idx in range(len(dataframe.index)):
            row = dataframe.iloc[idx]
            pid = row.get('PARTICIPANT_ID')
            serial = row.get('FORM_SERIAL')

            participant = Participant.query.filter(
                Participant.participant_id == pid,
                Participant.participant_set == event.participant_set).first()

            if not participant:
                error_records += 1
                error_log.append({
                    'label': 'ERROR',
                    'message': gettext(
                        'Participant ID %(part_id)s was not found',
                        part_id=pid)
                })

                self.update_task_info(
                    total_records=total_records,
                    processed_records=processed_records,
                    error_records=error_records,
                    warning_records=warning_records,
                    error_log=error_log)

                continue

            if not serial:
                error_records += 1
                error_log.append({
                    'label': 'ERROR',
                    'message': gettext(
                        'No form serial number specified on line %(lineno)d',
                        lineno=idx+1)
                })

                self.update_task_info(
                    total_records=total_records,
                    processed_records=processed_records,
                    error_records=error_records,
                    warning_records=warning_records,
                    error_log=error_log)

                continue

            submission = Submission.query.filter(
                Submission.form == form, Submission.participant == participant,
                Submission.location == participant.location,
                Submission.deployment == event.deployment,
                Submission.event == event, Submission.serial_no == serial,
                Submission.submission_type == 'O').first()

            if not submission:
                submission = Submission(
                    form_id=form.id, participant_id=participant.id,
                    location_id=participant.location.id,
                    deployment_id=event.deployment.id, event_id=event.id,
                    submission_type='O', serial_no=serial, data={})
                submission.save()

            master = Submission.query.filter(
                Submission.form == form, Submission.participant_id == None,  # noqa
                Submission.location == participant.location,
                Submission.deployment == event.deployment,
                Submission.event == event, Submission.serial_no == serial,
                Submission.submission_type == 'M').first()

            if not master:
                master = Submission(
                    form_id=form.id, participant_id=None,
                    location_id=participant.location.id,
                    deployment_id=event.deployment.id, event_id=event.id,
                    submission_type='M', serial_no=serial, data={})
                master.save()

            processed_records += 1

            self.update_task_info(
                total_records=total_records,
                processed_records=processed_records,
                error_records=error_records,
                warning_records=warning_records,
                error_log=error_log)
