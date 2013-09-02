import csv
import magic
from rapidsms.models import Backend, Connection, Contact
from rapidsms.router.api import lookup_connections
from xlrd import open_workbook
from core.models import Location, Observer, ObserverRole, Partner

backends = Backend.objects.all()


def _get_contact(phone):
    '''Given a phone number, returns a RapidSMS Contact linked to all
    Connection instances having that identity on all backends.

    Parameters
    - phone: an international phone number

    Returns
    - a Contact instance that has among its connection_set all
    Connection instances using the supplied phone number as identity'''
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
    '''Given a row of import data, attempt to create or update an Observer
    instance with the specified observer_id, and attempt to create all related
    objects (Partner, ObserverRole and Contact, specifically), except for the
    Location.

    Parameters
    - observer_id: the observer id
    - name: the observer's name
    - phone1, phone2, phone3: up to three phone numbers that can be linked to
      the observer
    - role_name: the name of the observer's role
    - location_name: the location the observer is stationed at
    - location_type: the name of the location type
    - supervisor_id: the observer_id of the observer's supervisor. Due to how
      the observer data is populated, the supervisor's data *MUST* be loaded
      before any observers under that supervisor can be loaded properly.
    - gender: either 'M' or 'F'. Out-of-band values will be set to unspecified
    - partner_name: the name of the partner organization the observer is
      attached to.

    Returns
    - True if the observer could be saved, and False otherwise. If False is
    returned, the observer was set to a location that could not be found.'''
    # attempt to find the location
    try:
        location = Location.objects.get(name__iexact=location_name,
                                        type__name__iexact=location_type)
    except Location.DoesNotExist:
        return False

    # find or create an Observer instance with the specified observer id
    try:
        observer = Observer.objects.get(observer_id=observer_id)
    except Observer.DoesNotExist:
        observer = Observer(observer_id=observer_id)

    # attempt to find the supervisor.
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

    # find or create the role
    role = ObserverRole.objects.get_or_create(name__iexact=role_name)

    if not gender in ('M', 'F'):
        gender = 'U'

    # find or create the linked contact
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

    Returns:
    - a list of rows that could not be imported
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
    '''Imports observer data from a pre-Excel 2007 (.xls) file.

    Parameters:
    - uploaded_file: an UploadedFile instance

    Returns:
    - a list of rows that could not be imported.'''
    # open the workbook and get the first sheet
    book = open_workbook(uploaded_file)
    sheet = book.sheet_by_index(0)

    errors = []

    # the first row is assumed to be the header, so skip it
    for index in range(1, sheet.nrows):
        row = sheet.row_values(index)

        if not _save_observer(*row):
            errors.append(row)

    return errors


action_map = {'text/plain': csv_import, 'text/csv': csv_import,
              'application/vnd.ms-office': excel_import,
              'application/vnd.ms-excel': excel_import}


def import_contacts(uploaded_file):
    '''Wrapper for importing observer data from either CSV or Excel files.
    If the file cannot be used for import, raises TypeError.

    Parameters:
    - uploaded_file: the uploaded file containing the observer data

    Returns:
    - a list of rows that could not be imported.'''
    # get file pointer location
    pos = uploaded_file.tell()

    mimetype = magic.from_buffer(uploaded_file.read(1024), mime=True)

    # reset file pointer
    uploaded_file.seek(pos)

    action = action_map.get(mimetype)

    if not action:
        raise TypeError('Invalid file format')

    return action(uploaded_file)
