from flask.ext.mail import Message
from apollo import services
from apollo.core import mail
from apollo.settings import SECURITY_EMAIL_SENDER
from apollo.messaging.outgoing import gateway_factory
from apollo.factory import create_celery_app


celery = create_celery_app()


@celery.task
def send_message(event, message, recipient, sender=""):
    """
    Task for sending outgoing messages using the configured gateway

    :param message: The string for the contents of the message to be sent
    :param recipient: The recipient of the text message
    :param sender: (Optional) The sender to set
    """
    gateway = gateway_factory()
    if gateway:
        services.messages.log_message(
            event=services.events.get(pk=event), recipient=recipient,
            sender=sender, text=message, direction='OUT')
        return gateway.send(message, recipient, sender)


@celery.task
def send_messages(event, message, recipients, sender=""):
    if hasattr(recipients, '__iter__'):
        items = [(event, message, recipient, sender)
                 for recipient in recipients]
        send_message.chunks(items, 100).delay()
    else:
        send_message.delay(event, message, recipients, sender)


@celery.task
def send_email(subject, body, recipients, sender=None):
    if not sender:
        sender = SECURITY_EMAIL_SENDER
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = body
    mail.send(msg)
