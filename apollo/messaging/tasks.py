# -*- coding: utf-8 -*-
from celery import shared_task
from flask_mail import Message
from sentry_sdk import capture_exception, capture_message

from apollo import models, services, settings
from apollo.core import mail
from apollo.messaging.outgoing import gateway_factory


@shared_task()
def send_message(event, message, recipient, sender=""):
    """Task for sending outgoing messages using the configured gateway.

    :param message: The string for the contents of the message to be sent
    :param recipient: The recipient of the text message
    :param sender: (Optional) The sender to set
    """
    gateway = gateway_factory()
    if gateway:
        services.messages.log_message(
            event=models.Event.query.filter_by(id=event).one(),
            recipient=recipient,
            sender=sender,
            text=message,
            direction="OUT",
        )
        return gateway.send(message, recipient, sender)


@shared_task()
def send_messages(event, message, recipients, sender=""):
    """Send an outgoing message."""
    try:
        _ = iter(recipients)
        items = [(event, message, recipient, sender) for recipient in set(recipients)]
        send_message.chunks(items, 100).delay()
    except TypeError:
        send_message.delay(event, message, recipients, sender)


@shared_task()
def send_email(subject, body, recipients, sender=None):
    """Send an outgoing email."""
    if not (settings.MAIL_SERVER or settings.MAIL_PORT or settings.MAIL_USERNAME):
        capture_message("No email server configured")
        return

    if not sender:
        sender = settings.SECURITY_EMAIL_SENDER
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = body
    try:
        mail.send(msg)
    except Exception:
        # still log the exception to Sentry,
        # but don't let it be uncaught
        capture_exception()
