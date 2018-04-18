# -*- coding: utf-8 -*-
import logging
import os
import random
import string

from flask import render_template_string
from flask_babelex import lazy_gettext as _
import pandas as pd
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from apollo import helpers, services
from apollo.core import uploads
from apollo.factory import create_celery_app
from apollo.messaging.tasks import send_email
from apollo.participants import utils
from apollo.participants.models import Participant

APPLICABLE_GENDERS = [s[0] for s in Participant.GENDER]
celery = create_celery_app()
logger = logging.getLogger(__name__)

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


def create_partner(name, participant_set):
    return services.participant_partners.create(
        name=name, participant_set_id=participant_set.id)


def create_group_type(name, participant_set):
    return services.participant_group_types.create(
        name=name, participant_set_id=participant_set.id)


def create_group(name, group_type, participant_set):
    return services.participant_groups.create(
        name=name, group_type_id=group_type.id,
        participant_set_id=participant_set.id)


def create_role(name, participant_set):
    return services.participant_roles.create(
        name=name,  participant_set_id=participant_set.id)


def generate_password(length):
    return ''.join(random.choice(
        string.ascii_uppercase + string.digits + string.ascii_lowercase)
        for _ in range(length))


def update_participants(dataframe, header_map, participant_set):
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
    index = dataframe.index

    unresolved_supervisors = set()
    errors = set()
    warnings = set()

    location_set = participant_set.location_set

    # set up mappings
    PARTICIPANT_ID_COL = header_map['id']
    NAME_COL = header_map.get('name')
    ROLE_COL = header_map.get('role')
    PARTNER_COL = header_map.get('partner')
    LOCATION_ID_COL = header_map.get('location')
    SUPERVISOR_ID_COL = header_map.get('supervisor')
    GENDER_COL = header_map.get('gender')
    EMAIL_COL = header_map.get('email')
    PASSWORD_COL = header_map.get('password')
    phone_columns = header_map.get('phone', [])
    group_columns = header_map.get('group', [])
    sample_columns = header_map.get('sample', [])

    extra_field_names = [f.name for f in participant_set.extra_fields] \
        if participant_set.extra_fields else []

    for idx in index:
        record = dataframe.ix[idx]
        participant_id = record[PARTICIPANT_ID_COL]
        if type(participant_id) == float:
            participant_id = int(participant_id)
        participant = services.participants.find(
            participant_id=str(participant_id),
            participant_set=participant_set
        ).first()

        if participant is None:
            participant = services.participants.new(
                participant_id=str(participant_id),
                participant_set_id=participant_set.id
            )

        if NAME_COL:
            name = record[NAME_COL]
            participant.name = name if _is_valid(name) else ''

        role = None
        if ROLE_COL:
            role_name = record[ROLE_COL]
            if _is_valid(role_name):
                role = services.participant_roles.find(
                    name=role_name,
                    participant_set=participant_set
                ).first()
                if role is None:
                    role = create_role(role_name, participant_set)
            participant.role = role

        partner = None
        if PARTNER_COL:
            partner_name = record[PARTNER_COL]
            if _is_valid(partner_name):
                partner = services.participant_partners.find(
                    name=partner_name,
                    participant_set=participant_set
                ).first()
                if partner is None:
                    partner = create_partner(partner_name, participant_set)
                participant.partner = partner

        location = None
        try:
            if LOCATION_ID_COL:
                loc_code = record[LOCATION_ID_COL]
                if isinstance(loc_code, float):
                    loc_code = int(loc_code)
                location = services.locations.find(
                    code=str(loc_code),
                    location_set=location_set
                ).one()
        except MultipleResultsFound:
            errors.add((
                participant_id,
                _('Invalid location id (%(loc_id)s)',
                    loc_id=record[LOCATION_ID_COL])
            ))
            continue
        except NoResultFound:
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
                    supervisor = services.participants.find(
                        participant_id=str(supervisor_id),
                        participant_set=participant_set,
                    ).first()
                    if supervisor is None:
                        # perhaps supervisor exists further along.
                        # cache the refs
                        unresolved_supervisors.add(
                            (participant_id, supervisor_id)
                        )
                    else:
                        participant.supervisor_id = supervisor.id

        if GENDER_COL:
            gender_spec = record[GENDER_COL]
            if _is_valid(gender_spec) and gender_spec.upper() in \
                    APPLICABLE_GENDERS:
                participant.gender = gender_spec.upper()
            else:
                participant.gender = APPLICABLE_GENDERS[0]

        if EMAIL_COL:
            participant.email = record[EMAIL_COL] \
                if _is_valid(record[EMAIL_COL]) else None

        if PASSWORD_COL:
            participant.password = record[PASSWORD_COL] \
                if _is_valid(record[PASSWORD_COL]) else generate_password(6)
        else:
            participant.password = generate_password(6)

        # save if this is a new participant - we need an id for lookup
        if not participant.id:
            participant.save()

        if phone_columns:
            # check if the phone number is on record
            for column in phone_columns:
                if not _is_valid(record[column]):
                    continue

                mobile = record[column]
                if isinstance(mobile, float):
                    mobile = int(mobile)
                mobile_num = str(mobile)

                phone = services.phones.get_by_number(mobile_num)
                if not phone:
                    phone = services.phones.create(number=mobile_num)

                p_phone = services.participant_phones.find(
                    participant_id=participant.id, phone_id=phone.id).first()
                if not p_phone:
                    services.participant_phones.create(
                        participant_id=participant.id,
                        phone_id=phone.id, verified=True)

        groups = []
        # fix up groups
        if group_columns:
            for column in group_columns:
                if not _is_valid(record[column]):
                    continue

                group_type = services.participant_group_types.find(
                    name=column,
                    participant_set=participant_set
                ).first()

                if not group_type:
                    group_type = create_group_type(
                        column, participant_set)

                group = services.participant_groups.find(
                    name=record[column],
                    group_type=group_type,
                    participant_set=participant_set).first()

                if not group:
                    group = create_group(
                        record[column], group_type, participant_set)

                groups.append(group)

            # if group_columns:
            #     participant.groups.extend(groups)

        # sort out any extra fields
        extra_data = {}
        for field_name in extra_field_names:
            column = header_map.get(field_name)
            if column:
                value = record[column]
                if _is_valid(value):
                    if isinstance(value, float):
                        value = int(value)
                    extra_data[field_name] = value

        # finally done with first pass
        participant.save()

        # if we have extra data, update the participant
        if extra_data:
            services.participants.find(id=participant.id).update(
                {'extra_data': extra_data}, synchronize_session=False)

        if groups:
            if participant.groups:
                participant.groups.extend(groups)
            else:
                participant.groups = groups
            participant.save()

    # second pass - resolve missing supervisor references
    for participant_id, supervisor_id in unresolved_supervisors:
        participant = services.participants.find(
            participant_id=participant_id,
            participant_set=participant_set
        ).first()
        supervisor = services.participants.find(
            participant_id=supervisor_id,
            participant_set=participant_set,
        ).first()

        if supervisor is None:
            participant.delete()
            errors.add((
                participant_id,
                _('Supervisor with ID %(id)s not found', id=supervisor_id)))
        else:
            participant.supervisor_id = supervisor.id
            participant.save()

    return dataframe.shape[0], errors, warnings


# def update_participants(dataframe, header_map, participant_set):
#     """
#     Given a Pandas `class`DataFrame that has participant information loaded,
#     create or update the participant database with the info contained therein.

#     The dataframe columns will have to be mapped to the data model attributes
#     via the `param header_map` argument, a dictionary with the following keys:
#         participant_id - the participant ID,
#         name - the participant's name
#         role - the participant's role. created if missing.
#         partner_org - the partner organization. created if missing.
#         location_id - the location code. if missing or not found,
#             is not set/updated.
#         supervisor_id - the participant's supervisor's ID. if not found on
#             loading the participant setting it is deferred.
#         gender - the participant's gender.
#         email - the participant's email.
#         password - the participant's password.
#         phone - a prefix for columns starting with this string that contain
#                 numbers
#         group - a prefix for columns starting with this string that contain
#                 participant group names
#     """
#     index = dataframe.index

#     unresolved_supervisors = set()
#     errors = set()
#     warnings = set()

#     location_set = participant_set.location_set

#     # set up mappings
#     PARTICIPANT_ID_COL = header_map['participant_id']
#     NAME_COL = header_map.get('name')
#     ROLE_COL = header_map.get('role')
#     PARTNER_COL = header_map.get('partner_org')
#     LOCATION_ID_COL = header_map.get('location_id')
#     SUPERVISOR_ID_COL = header_map.get('supervisor_id')
#     GENDER_COL = header_map.get('gender')
#     EMAIL_COL = header_map.get('email')
#     PASSWORD_COL = header_map.get('password')
#     PHONE_PREFIX = header_map.get('phone')
#     GROUP_PREFIX = header_map.get('group')

#     extra_field_names = [f.name for f in participant_set.extra_fields] \
#         if participant_set.extra_fields else []

#     phone_columns = [c for c in dataframe.columns
#                      if c.startswith(PHONE_PREFIX)]
#     group_columns = [c for c in dataframe.columns
#                      if c.startswith(GROUP_PREFIX)] if GROUP_PREFIX else []

#     for idx in index:
#         record = dataframe.ix[idx]
#         participant_id = record[PARTICIPANT_ID_COL]
#         if type(participant_id) == float:
#             participant_id = int(participant_id)
#         participant = services.participants.find(
#             participant_id=str(participant_id),
#             participant_set=participant_set
#         ).first()

#         if participant is None:
#             participant = services.participants.new(
#                 participant_id=str(participant_id),
#                 participant_set_id=participant_set.id
#             )

#         if NAME_COL:
#             name = record[NAME_COL]
#             participant.name = name if _is_valid(name) else ''

#         role = None
#         if ROLE_COL:
#             role_name = record[ROLE_COL]
#             if _is_valid(role_name):
#                 role = services.participant_roles.find(
#                     name=role_name,
#                     participant_set=participant_set
#                 ).first()
#                 if role is None:
#                     role = create_role(role_name, participant_set)
#             participant.role = role

#         partner = None
#         if PARTNER_COL:
#             partner_name = record[PARTNER_COL]
#             if _is_valid(partner_name):
#                 partner = services.participant_partners.find(
#                     name=partner_name,
#                     participant_set=participant_set
#                 ).first()
#                 if partner is None:
#                     partner = create_partner(partner_name, participant_set)
#                 participant.partner = partner

#         location = None
#         try:
#             if LOCATION_ID_COL:
#                 loc_code = record[LOCATION_ID_COL]
#                 if isinstance(loc_code, float):
#                     loc_code = int(loc_code)
#                 location = services.locations.find(
#                     code=str(loc_code),
#                     location_set=location_set
#                 ).one()
#         except MultipleResultsFound:
#             errors.add((
#                 participant_id,
#                 _('Invalid location id (%(loc_id)s)',
#                     loc_id=record[LOCATION_ID_COL])
#             ))
#             continue
#         except NoResultFound:
#             warnings.add((
#                 participant_id,
#                 _('Location with id %(loc_id)s not found',
#                     loc_id=record[LOCATION_ID_COL])
#             ))

#         if location:
#             participant.location = location

#         supervisor = None
#         if SUPERVISOR_ID_COL:
#             if _is_valid(record[SUPERVISOR_ID_COL]):
#                 if record[SUPERVISOR_ID_COL] != participant_id:
#                     # ignore cases where participant is own supervisor
#                     supervisor_id = record[SUPERVISOR_ID_COL]
#                     if type(supervisor_id) == float:
#                         supervisor_id = int(supervisor_id)
#                     supervisor = services.participants.find(
#                         participant_id=str(supervisor_id),
#                         participant_set=participant_set,
#                     ).first()
#                     if supervisor is None:
#                         # perhaps supervisor exists further along.
#                         # cache the refs
#                         unresolved_supervisors.add(
#                             (participant_id, supervisor_id)
#                         )
#                     else:
#                         participant.supervisor_id = supervisor.id

#         if GENDER_COL:
#             gender_spec = record[GENDER_COL]
#             if _is_valid(gender_spec) and gender_spec.upper() in \
#                     APPLICABLE_GENDERS:
#                 participant.gender = gender_spec.upper()
#             else:
#                 participant.gender = APPLICABLE_GENDERS[0]

#         if EMAIL_COL:
#             participant.email = record[EMAIL_COL] \
#                 if _is_valid(record[EMAIL_COL]) else None

#         if PASSWORD_COL:
#             participant.password = record[PASSWORD_COL] \
#                 if _is_valid(record[PASSWORD_COL]) else generate_password(6)
#         else:
#             participant.password = generate_password(6)

#         # save if this is a new participant - we need an id for lookup
#         if not participant.id:
#             participant.save()

#         if PHONE_PREFIX:
#             # check if the phone number is on record
#             for column in phone_columns:
#                 if not _is_valid(record[column]):
#                     continue

#                 mobile = record[column]
#                 if isinstance(mobile, float):
#                     mobile = int(mobile)
#                 mobile_num = str(mobile)

#                 phone = services.phones.get_by_number(mobile_num)
#                 if not phone:
#                     phone = services.phones.create(number=mobile_num)

#                 p_phone = services.participant_phones.find(
#                     participant_id=participant.id, phone_id=phone.id).first()
#                 if not p_phone:
#                     services.participant_phones.create(
#                         participant_id=participant.id,
#                         phone_id=phone.id, verified=True)

#         groups = []
#         # fix up groups
#         if GROUP_PREFIX:
#             for column in group_columns:
#                 if not _is_valid(record[column]):
#                     continue

#                 group_type = services.participant_group_types.find(
#                     name=column,
#                     participant_set=participant_set
#                 ).first()

#                 if not group_type:
#                     group_type = create_group_type(
#                         column, participant_set)

#                 group = services.participant_groups.find(
#                     name=record[column],
#                     group_type=group_type,
#                     participant_set=participant_set).first()

#                 if not group:
#                     group = create_group(
#                         record[column], group_type, participant_set)

#                 groups.append(group)

#             # if group_columns:
#             #     participant.groups.extend(groups)

#         # sort out any extra fields
#         extra_data = {}
#         for field_name in extra_field_names:
#             column = header_map.get(field_name)
#             if column:
#                 value = record[column]
#                 if _is_valid(value):
#                     if isinstance(value, float):
#                         value = int(value)
#                     extra_data[field_name] = value

#         # finally done with first pass
#         participant.save()

#         # if we have extra data, update the participant
#         if extra_data:
#             services.participants.find(id=participant.id).update(
#                 {'extra_data': extra_data}, synchronize_session=False)

#         if groups:
#             if participant.groups:
#                 participant.groups.extend(groups)
#             else:
#                 participant.groups = groups
#             participant.save()

#     # second pass - resolve missing supervisor references
#     for participant_id, supervisor_id in unresolved_supervisors:
#         participant = services.participants.find(
#             participant_id=participant_id,
#             participant_set=participant_set
#         ).first()
#         supervisor = services.participants.find(
#             participant_id=supervisor_id,
#             participant_set=participant_set,
#         ).first()

#         if supervisor is None:
#             participant.delete()
#             errors.add((
#                 participant_id,
#                 _('Supervisor with ID %(id)s not found', id=supervisor_id)))
#         else:
#             participant.supervisor_id = supervisor.id
#             participant.save()

#     return dataframe.shape[0], errors, warnings


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
def import_participants(upload_id, mappings, participant_set_id):
    upload = services.user_uploads.find(id=upload_id).first()
    if not upload:
        logger.error('Upload %s does not exist, aborting', upload_id)
        return

    filepath = uploads.path(upload.upload_filename)
    if not os.path.exists(filepath):
        logger.error('Upload file %s does not exist, aborting', filepath)
        upload.delete()
        return

    with open(filepath) as f:
        dataframe = helpers.load_source_file(f)

    participant_set = services.participant_sets.find(
        id=participant_set_id).first()

    if not participant_set:
        _cleanup_upload(filepath, upload)
        logger.error(
            'Participant set with id {} does not exist, aborting'.format(
                participant_set_id))

    count, errors, warnings = update_participants(
        dataframe,
        mappings,
        participant_set
    )

    # delete uploaded file
    os.remove(filepath)
    upload.delete()

    msg_body = generate_response_email(count, errors, warnings)

    send_email(_('Import report'), msg_body, [upload.user.email])


@celery.task
def nuke_participants(participant_set_id):
    participant_set = services.participant_sets.find(
        id=participant_set_id).first()
    if participant_set:
        utils.nuke_participants(participant_set)


def _cleanup_upload(filepath, upload):
    os.remove(filepath)
    upload.delete()
