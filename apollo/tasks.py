# -*- coding: utf-8 -*-
from apollo.factory import create_celery_app

celery = create_celery_app()

from apollo.deployments.tasks import delete_event  # noqa
from apollo.formsframework.tasks import update_submissions  # noqa
from apollo.messaging.tasks import send_messages, send_email  # noqa
from apollo.participants.tasks import import_participants  # noqa
from apollo.locations.tasks import import_locations  # noqa
from apollo.submissions.tasks import init_submissions  # noqa
