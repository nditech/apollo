from celery import task
from django.conf import settings
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.router.api import lookup_connections


def _send_message(connection, message):
    msg = OutgoingMessage(connection, message)
    return msg.send()


@task
def outboundsms_task(recipient, message):
    '''Performs out-of-band sending of messages.

    Parameters
    - recipient: a string or iterable of strings, the numbers to send sms to.
    - message: the message to be sent'''

    numbers = []

    if isinstance(recipient, basestring):
        numbers.append(recipient)
    else:
        numbers.extend(recipient)

    # TODO: needs refactoring
    connections = lookup_connections(settings.OUTBOUNDSMS_BACKEND, numbers)

    for connection in connections:
        _send_message(connection, message)
