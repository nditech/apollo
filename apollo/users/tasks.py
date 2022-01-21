# -*- coding: utf-8 -*-
from apollo.factory import create_celery_app
from apollo.users.models import User

celery = create_celery_app()


@celery.task(bind=True)
def import_users(self, dataset, deployment_id):
    User.import_user_list(dataset, deployment_id, self)
