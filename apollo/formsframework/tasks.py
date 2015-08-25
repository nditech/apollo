from .. import services
from ..factory import create_celery_app

celery = create_celery_app()


@celery.task
def update_submissions(form_pk):
    '''
    Updates submissions after a form has been updated, so all the fields
    in the form are existent in the submissions.
    '''
    form = services.forms.get(pk=form_pk)
    tags = form.tags
    for submission in services.submissions.find(form=form):
        for tag in tags:
            if not hasattr(submission, tag):
                setattr(submission, tag, None)
        submission.save()
