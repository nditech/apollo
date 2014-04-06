from .outgoing import gateway_factory


def send_message(message, recipients, sender=""):
    """
    Task for sending outgoing messages using the configured gateway

    :param message: The string for the contents of the message to be sent
    :param recipients: An array of all the phone numbers of the recipients
    :param sender: (Optional) The sender to set
    """
    gateway = gateway_factory()
    if gateway:
        return gateway.send(message, recipients, sender)
