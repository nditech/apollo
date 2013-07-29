import re
from apollo.core.models import *
from django.conf import settings
from rapidsms.models import Connection, Backend
from rapidsms.router.api import send


def get_bulksms_backend(phone):
    backend_name = settings.BULKSMS_ROUTES.get('default', settings.BULKSMS_BACKEND)
    routes = settings.BULKSMS_ROUTES
    for prefix in filter(lambda r: r != "default", routes.keys()):
        if re.match(prefix, phone):
            backend_name = settings.BULKSMS_ROUTES.get(prefix)
            break
    return Backend.objects.get_or_create(name=backend_name)[0]


def send_bulk_message(observers, message):
    connections = []
    for observer in Observer.objects.filter(pk__in=observers).values('contact__connection__identity', 'contact').distinct():
        if observer.get('contact__connection__identity', None):
            phone = observer.get('contact__connection__identity')
            contact = Contact.objects.get(pk=observer.get('contact'))
            backend = get_bulksms_backend(phone)

            connection = Connection.objects.get_or_create(
                identity=phone, backend=backend, contact=contact)[0]
            connections.append(connection)
    # append numbers to be copied on every message
    for phone in settings.PHONE_CC:
        backend = get_bulksms_backend(phone)
        connection = Connection.objects.get_or_create(
            identity=phone, backend=backend)[0]
        connections.append(connection)
    if connections:
        send(message, connections)
