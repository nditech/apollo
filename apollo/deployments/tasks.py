# -*- coding: utf-8 -*-
from apollo import models
from apollo.core import db
from apollo.factory import create_celery_app

celery = create_celery_app()


@celery.task
def delete_event(event_pk: int) -> None:
    events_table = models.Event.__table__
    messages_table = models.Message.__table__
    submissions_table = models.Submission.__table__

    engine = db.get_engine()

    try:
        # create a transaction. an exception while the context manager is
        # active will cause the transaction to be rolled back, and the
        # exception will be propagated outwards
        with engine.begin() as connection:
            # generate the SQL statements to delete:
            # - messages (linked to the event)
            messages_delete_st = messages_table.delete().where(
                messages_table.c.event_id == event_pk
            )
            # - submissions (linked to the event)
            submissions_delete_st = submissions_table.delete().where(
                submissions_table.c.event_id == event_pk
            )
            # - the event itself
            event_delete_st = events_table.delete().where(
                events_table.c.id == event_pk
            )

            # delete each in a sub-transaction
            try:
                with connection.begin():
                    connection.execute(messages_delete_st)
            except Exception:
                return

            try:
                with connection.begin():
                    connection.execute(submissions_delete_st)
            except Exception:
                return

            try:
                with connection.begin():
                    connection.execute(event_delete_st)
            except Exception:
                return
    except Exception:
        return
