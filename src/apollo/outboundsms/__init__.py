from outboundsms.tasks import outboundsms_task


def send_sms(recipient, message):
    '''Wraps message sending functionality so other modules can easily
    use it.

    Parameters:
    - recipient: a string/iterable of strings, with numbers to send to
    - message: the message to send.'''

    if not isinstance(recipient, (basestring, list, tuple)):
        raise TypeError('Expected a string, list or tuple')

    outboundsms_task(recipient, message)
