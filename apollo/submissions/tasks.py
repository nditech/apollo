from apollo import models
from apollo.factory import create_celery_app


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
