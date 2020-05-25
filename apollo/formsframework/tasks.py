# -*- coding: utf-8 -*-
from ..factory import create_celery_app
from .. import core, models


celery = create_celery_app()


@celery.task
def delete_form(form_id):
    '''
    Deletes linked submissions and deletes the form as well
    '''
    models.Submission.query.filter(
        models.Submission.form_id == form_id).delete()
    models.Form.query.filter(models.Form.id == form_id).delete()

    core.db.session.commit()
