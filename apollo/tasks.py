from .factory import create_celery_app
from .messaging.tasks import send_message, send_email
from .participants.tasks import import_participants

celery = create_celery_app()

send_email = celery.task(send_email)
send_message = celery.task(send_message)
import_participants = celery.task(import_participants)
