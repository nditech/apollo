# -*- coding: utf-8 -*-
from functools import partial

from mongoengine import signals

from apollo import models
from apollo.factory import create_celery_app
from apollo.formsframework.forms import update_submission_version
from apollo.participants.utils import update_participant_completion_rating


celery = create_celery_app()


@celery.task
def init_submissions(deployment_pk, event_pk, form_pk, role_pk,
                     location_type_pk):
    deployment = models.Deployment.objects.get(pk=deployment_pk)
    event = models.Event.objects.get(pk=event_pk)
    form = models.Form.objects.get(pk=form_pk)
    role = models.ParticipantRole.objects.get(pk=role_pk)
    location_type = models.LocationType.objects.get(pk=location_type_pk)

    if not (deployment and event and form and role and location_type):
        return

    models.Submission.init_submissions(deployment, event, form,
                                       role, location_type)


@celery.task
def update_submission(submission_pk, sender):
    try:
        submission = models.Submission.objects.get(pk=submission_pk)
    except models.Submission.DoesNotExist:
        return

    post_save_handler = partial(update_submission_version, sender)

    with signals.post_save.connected_to(
            post_save_handler,
            sender=models.Submission):
        # save with precomputation enabled
        submission.save()

    # update completion rating for participant
    if submission.form.form_type == 'CHECKLIST':
        participant = submission.contributor
        if participant:
            update_participant_completion_rating(participant)
