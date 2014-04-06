from .factory import create_celery_app
from .messaging.tasks import send_message

celery = create_celery_app()

send_message = celery.task(send_message)
