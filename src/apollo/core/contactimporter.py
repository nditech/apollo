import csv
import magic
from rapidsms.models import Backend, Connection, Contact
from rapidsms.router.api import lookup_connections
from xlrd import open_workbook
from core.models import Location, Observer, ObserverRole, Partner

backends = Backend.objects.all()


def _get_contact(phone):
    connections = Connection.objects.filter(identity=phone)

    if connections:
        contact = connections[0].contact

        if contact:
            return contact

        contact = Contact.objects.create()
        contact.connection_set.add(*connections)

        return contact

    contact = Contact.objects.create()

    for backend in backends:
        connections = lookup_connections(backend, phone)

        contact.connection_set.add(connections)

    return contact


def _save_observer(observer_id, name, phone1, phone2, phone3, role_name,
                   location_name, location_type, supervisor_id, gender,
                   partner_name):
    # attempt to find the location
    try:
        location = Location.objects.get(name__iexact=location_name,
                                        type__name=location_type)
    except Location.DoesNotExist:
        return False

    # first, attempt to find the observer
    try:
        observer = Observer.objects.get(observer_id=observer_id)
    except Observer.DoesNotExist:
        observer = Observer(observer_id=observer_id)

    # attempt to find the supervisor
    try:
        supervisor = Observer.objects.get(observer_id=supervisor_id)
    except Observer.DoesNotExist:
        supervisor = None

    # attempt to find the partner, or create it
    try:
        partner = Partner.objects.get(name__iexact=partner_name)
    except Partner.DoesNotExist:
        partner = Partner.objects.create(name=partner_name,
                                         abbr=partner_name[:5].upper())

    role = ObserverRole.objects.get_or_create(name__iexact=role_name)

    if not gender in ('M', 'F'):
        gender = 'U'

    contact = _get_contact(phone1)

    if phone2:
        contact = _get_contact(phone2)

    if phone3:
        contact = _get_contact(phone3)

    # create/update the observer
    observer.location = location
    observer.name = name
    observer.contact = contact
    observer.role = role
    observer.supervisor = supervisor
    observer.gender = gender
    observer.partner = partner

    observer.save()

    return True


def csv_import(uploaded_file):
    '''Imports observer data from a CSV file and persists it.

    Parameters:
    - uploaded_file: an UploadedFile instance
    '''
    reader = csv.DictReader(uploaded_file)
    errors = []

    for row in reader:
        observer_id = row['Observer ID']
        name = row['Name']
        phone1 = row['Phone 1']
        phone2 = row['Phone 2']
        phone3 = row['Phone 3']
        role_name = row['Role']
        location_name = row['Location']
        location_type = row['Location Type']
        supervisor_id = row['Supervisor ID']
        gender = row['Gender']
        partner_name = row['Partner']

        if not _save_observer(observer_id, name, phone1, phone2, phone3,
                              role_name, location_name, location_type,
                              supervisor_id, gender, partner_name):
            errors.append(row)

    return errors


def excel_import(uploaded_file):
    # open the workbook and get the first sheet
    book = open_workbook(uploaded_file)
    sheet = book.sheet_by_index(0)

    errors = []

    for index in range(1, sheet.nrows):
        row = sheet.row_values(index)

        if not _save_observer(*row):
            errors.append(row)

    return errors


action_map = {'text/plain': csv_import, 'text/csv': csv_import,
              'application/vnd.ms-office': excel_import,
              'application/vnd.ms-excel': excel_import}


def import_contacts(uploaded_file):
    # get file pointer location
    pos = uploaded_file.tell()

    mimetype = magic.from_buffer(uploaded_file.read(1024), mime=True)

    # reset file pointer
    uploaded_file.seek(pos)

    action = action_map.get(mimetype)

    if not action:
        raise TypeError('Invalid file format')

    return action(uploaded_file)
