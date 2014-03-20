from .core import mail
from .factory import create_celery_app

celery = create_celery_app()


@celery.task
def does_nothing():
    """Does absolutely nothing"""
    pass
