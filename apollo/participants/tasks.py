from collections import OrderedDict
from flask import render_template_string
from flask.ext.babel import lazy_gettext as _
from mongoengine import MultipleObjectsReturned
import pandas as pd
from apollo.messaging.tasks import send_email
from apollo import services, helpers
from apollo.factory import create_celery_app
from apollo.participants.models import PhoneContact
import random
import string

celery = create_celery_app()

email_template = '''
Of {{ count }} records, {{ successful_imports }} were successfully imported, {{ suspect_imports }} raised warnings, and {{ unsuccessful_imports }} could not be imported.
{% if errors %}
The following records could not be imported:
-------------------------
{% for e in errors %}
{%- set pid = e[0] %}{% set msg = e[1] -%}
Record for participant ID {{ pid }} raised error: {{ msg }}
{% endfor %}
{% endif %}

{% if warnings %}
The following records raised warnings:
{% for e in warnings %}
{%- set pid = e[0] %}{% set msg = e[1] -%}
Record for participant ID {{ pid }} raised warning: {{ msg }}
{% endfor %}
{% endif %}
'''


def _is_valid(item):
    return not pd.isnull(item) and item


def create_partner(name, deployment):
    return services.participant_partners.create(
        name=name,
        deployment=deployment)


def create_group_type(name, deployment):
    return services.participant_group_types.create(
        name=name,
        deployment=deployment)


def create_group(name, group_type, deployment):
    return services.participant_groups.create(
        name=name,
        group_type=group_type.name,
        deployment=deployment)


def create_role(name, deployment):
    return services.participant_roles.create(name=name,
                                             deployment=deployment)

def generate_password(length):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(length))

def update_participants(dataframe, event, header_map):
    """
    Given a Pandas `class`DataFrame that has participant information loaded,
    create or update the participant database with the info contained therein.

    The dataframe columns will have to be mapped to the data model attributes
    via the `param header_map` argument, a dictionary with the following keys:
        participant_id - the participant ID,
        name - the participant's name
        role - the participant's role. created if missing.
        partner_org - the partner organization. created if missing.
        location_id - the location code. if missing or not found,
            is not set/updated.
        supervisor_id - the participant's supervisor's ID. if not found on
            loading the participant setting it is deferred.
        gender - the participant's gender.
        email - the participant's email.
        password - the participant's password.
        phone - a prefix for columns starting with this string that contain
                numbers
        group - a prefix for columns starting with this string that contain
                participant group names
    """
    deployment = event.deployment
    index = dataframe.index

    unresolved_supervisors = set()
    errors = set()
    warnings = set()

    # set up mappings
    PARTICIPANT_ID_COL = header_map['participant_id']
    NAME_COL = header_map.get('name')
    ROLE_COL = header_map.get('role')
    PARTNER_COL = header_map.get('partner_org')
    LOCATION_ID_COL = header_map.get('location_id')
    SUPERVISOR_ID_COL = header_map.get('supervisor_id')
    GENDER_COL = header_map.get('gender')
    EMAIL_COL = header_map.get('email')
    PASSWORD_COL = header_map.get('password')
    PHONE_PREFIX = header_map.get('phone')
    GROUP_PREFIX = header_map.get('group')

    extra_field_names = [f.name for
                         f in event.deployment.participant_extra_fields]

    phone_columns = [c for c in dataframe.columns
                     if c.startswith(PHONE_PREFIX)]
    group_columns = [c for c in dataframe.columns
                     if c.startswith(GROUP_PREFIX)] if GROUP_PREFIX else []

    for idx in index:
        record = dataframe.ix[idx]
        participant_id = record[PARTICIPANT_ID_COL]
        if type(participant_id) == float:
            participant_id = int(participant_id)
        participant = services.participants.get(
            participant_id=unicode(participant_id),
            deployment=event.deployment,
            event=event
        )

        if participant is None:
            participant = services.participants.new(
                participant_id=unicode(participant_id),
                deployment=event.deployment,
                event=event
            )

        if NAME_COL:
            name = record[NAME_COL]
            participant.name = name if _is_valid(name) else ''

        role = None
        if ROLE_COL:
            role_name = record[ROLE_COL]
            if _is_valid(role_name):
                role = services.participant_roles.get(
                    name=role_name,
                    deployment=deployment
                )
                if role is None:
                    role = create_role(role_name, deployment)
            participant.role = role

        partner = None
        if PARTNER_COL:
            partner_name = record[PARTNER_COL]
            if _is_valid(partner_name):
                partner = services.participant_partners.get(
                    name=partner_name,
                    deployment=deployment
                )
                if partner is None:
                    partner = create_partner(partner_name, deployment)
                participant.partner = partner

        location = None
        try:
            if LOCATION_ID_COL:
                loc_code = record[LOCATION_ID_COL]
                if isinstance(loc_code, float):
                    loc_code = int(loc_code)
                location = services.locations.get(
                    code=unicode(loc_code),
                    deployment=deployment
                )
        except MultipleObjectsReturned:
            errors.add((
                participant_id,
                _('Invalid location id (%(loc_id)s)',
                    loc_id=record[LOCATION_ID_COL])
            ))
            continue

        if location is None and LOCATION_ID_COL:
            warnings.add((
                participant_id,
                _('Location with id %(loc_id)s not found',
                    loc_id=record[LOCATION_ID_COL])
            ))

        if location:
            participant.location = location

        supervisor = None
        if SUPERVISOR_ID_COL:
            if _is_valid(record[SUPERVISOR_ID_COL]):
                if record[SUPERVISOR_ID_COL] != participant_id:
                    # ignore cases where participant is own supervisor
                    supervisor_id = record[SUPERVISOR_ID_COL]
                    if type(supervisor_id) == float:
                        supervisor_id = int(supervisor_id)
                    supervisor = services.participants.get(
                        participant_id=unicode(supervisor_id),
                        event=event
                    )
                    if supervisor is None:
                        # perhaps supervisor exists further along.
                        # cache the refs
                        unresolved_supervisors.add(
                            (participant_id, unicode(supervisor_id))
                        )
            participant.supervisor = supervisor

        if GENDER_COL:
            participant.gender = record[GENDER_COL] \
                if _is_valid(record[GENDER_COL]) else ''

        if EMAIL_COL:
            participant.email = record[EMAIL_COL] \
                if _is_valid(record[EMAIL_COL]) else None

        if PASSWORD_COL:
            participant.password = record[PASSWORD_COL] \
                if _is_valid(record[PASSWORD_COL]) else generate_password(6)
        else:
            participant.password = generate_password(6)

        # wonky hacks to avoid doing addToSet queries
        # for events and phone numbers
        if PHONE_PREFIX:
            phone_info = OrderedDict()
            for phone in participant.phones:
                phone_info[phone.number] = phone.verified
            for column in phone_columns:
                if not _is_valid(record[column]):
                    continue
                mobile = record[column]
                if type(mobile) is float:
                    mobile = int(mobile)
                phone_info[mobile] = True

            phones = [
                PhoneContact(number=unicode(k),
                             verified=v) for k, v in phone_info.items()
            ]
            if phone_columns:
                participant.phones = phones

        # fix up groups
        if GROUP_PREFIX:
            groups = []
            for column in group_columns:
                group_type = services.participant_group_types.get(
                    name=column,
                    deployment=event.deployment
                )

                if not group_type:
                    group_type = create_group_type(column, event.deployment)

                if not _is_valid(record[column]):
                    continue

                group = services.participant_groups.get(
                    name=record[column],
                    group_type=group_type.name,
                    deployment=event.deployment)

                if not group:
                    group = create_group(
                        record[column], group_type, event.deployment)

                groups.append(group)

            if group_columns:
                participant.groups = groups

        # sort out any extra fields
        for field_name in extra_field_names:
            column = header_map.get(field_name)
            if column:
                value = record[column]
                if _is_valid(value):
                    if isinstance(value, float):
                        value = int(value)
                    setattr(participant, field_name, value)

        # finally done with first pass
        participant.save()

    # second pass - resolve missing supervisor references
    for participant_id, supervisor_id in unresolved_supervisors:
        participant = services.participants.get(
            participant_id=participant_id,
            event=event
        )
        supervisor = services.participants.get(
            participant_id=supervisor_id,
            event=event
        )

        if supervisor is None:
            participant.delete()
            errors.add((
                participant_id,
                _('Supervisor with ID %(id)s not found', id=supervisor_id)))
        else:
            participant.supervisor = supervisor
            participant.save()

    return dataframe.shape[0], errors, warnings


def generate_response_email(count, errors, warnings):
    unsuccessful_imports = len(errors)
    successful_imports = count - unsuccessful_imports
    suspect_imports = len(warnings)

    return render_template_string(
        email_template,
        count=count,
        errors=errors,
        warnings=warnings,
        successful_imports=successful_imports,
        unsuccessful_imports=unsuccessful_imports,
        suspect_imports=suspect_imports
    )


@celery.task
def import_participants(upload_id, mappings):
    upload = services.user_uploads.get(pk=upload_id)
    dataframe = helpers.load_source_file(upload.data)
    count, errors, warnings = update_participants(
        dataframe,
        upload.event,
        mappings
    )

    # delete uploaded file
    upload.data.delete()
    upload.delete()

    msg_body = generate_response_email(count, errors, warnings)

    send_email(_('Import report'), msg_body, [upload.user.email])
