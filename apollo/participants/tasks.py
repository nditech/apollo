# -*- coding: utf-8 -*-
import logging
import numbers
import os
import random
import string

from flask import render_template_string
from flask_babelex import gettext
from flask_babelex import lazy_gettext as _
import pandas as pd
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from apollo import helpers, services
from apollo.core import db, uploads
from apollo.factory import create_celery_app
from apollo.messaging.tasks import send_email
from apollo.participants.models import Participant, Sample

APPLICABLE_GENDERS = [s[0] for s in Participant.GENDER]
celery = create_celery_app()
logger = logging.getLogger(__name__)

email_template = '''
Of {{ count }} records:
- {{ successful_imports }} were successfully imported,
- {{ suspect_imports }} raised warnings,
- and {{ unsuccessful_imports }} could not be imported.

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


def create_role(name, participant_set):
    return services.participant_roles.create(
        name=name,  participant_set_id=participant_set.id)


def generate_password(length):
    return ''.join(random.choice(
        string.ascii_uppercase + string.digits + string.ascii_lowercase)
        for _ in range(length))


def update_participants(dataframe, header_map, participant_set, task):
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
    """
    index = dataframe.index

    unresolved_supervisors = set()
    errors = set()
    warnings = set()

    total_records = dataframe.shape[0]
    processed_records = 0
    error_records = 0
    warning_records = 0
    error_log = []

    location_set = participant_set.location_set
    locales = location_set.deployment.locale_codes
    full_name_column_keys = [
        f'full_name_{locale}'
        for locale in locales
    ]
    first_name_column_keys = [
        f'first_name_{locale}'
        for locale in locales
    ]
    other_names_column_keys = [
        f'other_names_{locale}'
        for locale in locales
    ]
    last_name_column_keys = [
        f'last_name_{locale}'
        for locale in locales
    ]

    # set up mappings
    PARTICIPANT_ID_COL = header_map['id']
    ROLE_COL = header_map.get('role')
    PARTNER_COL = header_map.get('partner')
    LOCATION_ID_COL = header_map.get('location')
    SUPERVISOR_ID_COL = header_map.get('supervisor')
    GENDER_COL = header_map.get('gender')
    EMAIL_COL = header_map.get('email')
    PASSWORD_COL = header_map.get('password')
    LOCALE_COL = header_map.get('locale')
    phone_columns = header_map.get('phone', [])
    sample_columns = header_map.get('sample', [])
    full_name_columns = [
        header_map.get(col) for col in full_name_column_keys]
    first_name_columns = [
        header_map.get(col) for col in first_name_column_keys]
    other_names_columns = [
        header_map.get(col) for col in other_names_column_keys]
    last_name_columns = [
        header_map.get(col) for col in last_name_column_keys]

    extra_field_names = [f.name for f in participant_set.extra_fields] \
        if participant_set.extra_fields else []

    sample_map = {}
    # clear existing samples
    Sample.query.filter_by(participant_set_id=participant_set.id).delete()
    db.session.commit()

    # and create new ones
    if sample_columns:
        sample_map.update({
            n: Sample(name=n, participant_set=participant_set)
            for n in sample_columns if _is_valid(n)
        })
        db.session.add_all(sample_map.values())
        db.session.commit()

    for idx in index:
        record = dataframe.iloc[idx]
        participant_id = record[PARTICIPANT_ID_COL]
        try:
            participant_id = int(participant_id)
        except (TypeError, ValueError):
            message = gettext(
                'Invalid (non-numeric) participant ID (%(p_id)s)',
                p_id=participant_id)
            errors.add(
                (participant_id, message)
            )
            error_records += 1
            error_log.append({
                'label': 'ERROR',
                'message': message
            })
            continue
        participant_id = str(participant_id)

        participant = services.participants.find(
            participant_id=participant_id,
            participant_set=participant_set
        ).first()

        if participant is None:
            participant = services.participants.new(
                participant_id=participant_id,
                participant_set_id=participant_set.id
            )

        participant_full_names = [record.get(col) for col in full_name_columns]
        if participant_full_names:
            participant.full_name_translations = {
                locale: str(name).strip()
                for locale, name in zip(locales, participant_full_names)
                if _is_valid(name)
            }

        participant_first_names = [
            record.get(col) for col in first_name_columns
        ]
        if participant_first_names:
            participant.first_name_translations = {
                locale: str(name).strip()
                for locale, name in zip(locales, participant_first_names)
                if _is_valid(name)
            }

        participant_other_names = [
            record.get(col) for col in other_names_columns
        ]
        if participant_other_names:
            participant.other_names_translations = {
                locale: str(name).strip()
                for locale, name in zip(locales, participant_other_names)
                if _is_valid(name)
            }

        participant_last_names = [
            record.get(col)
            for col in last_name_columns
        ]
        if participant_last_names:
            participant.last_name_translations = {
                locale: str(name).strip()
                for locale, name in zip(locales, participant_last_names)
                if _is_valid(name)
            }

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
                try:
                    loc_code = int(loc_code)
                except (TypeError, ValueError):
                    message = gettext(
                        'Invalid (non-numeric) location ID (%(loc_id)s)',
                        loc_id=loc_code)
                    errors.add((participant_id, message))
                    error_records += 1
                    error_log.append({
                        'label': 'ERROR',
                        'message': message
                    })
                    continue

                location = services.locations.find(
                    code=str(loc_code),
                    location_set=location_set
                ).one()
        except MultipleResultsFound:
            errors.add((
                participant_id,
                gettext('Invalid location id (%(loc_id)s)',
                        loc_id=record[LOCATION_ID_COL])
            ))
            error_records += 1
            error_log.append({
                'label': 'ERROR',
                'message': gettext(
                    'Location code %(loc_id)s for row %(row)d is not unique',
                    loc_id=record[LOCATION_ID_COL], row=(idx + 1)),
            })
            continue
        except NoResultFound:
            warnings.add((
                participant_id,
                gettext('Location with id %(loc_id)s not found',
                        loc_id=record[LOCATION_ID_COL])
            ))
            warning_records += 1
            error_log.append({
                'label': 'WARNING',
                'message': gettext(
                    'Location code %(loc_id)s for row %(row)d with '
                    'participant ID %(part_id)s not found',
                    loc_id=record[LOCATION_ID_COL], row=(idx + 1),
                    part_id=record[PARTICIPANT_ID_COL])
            })

        if location:
            participant.location = location

        supervisor = None
        if SUPERVISOR_ID_COL:
            if _is_valid(record[SUPERVISOR_ID_COL]):
                if record[SUPERVISOR_ID_COL] != participant_id:
                    # ignore cases where participant is own supervisor
                    supervisor_id = record[SUPERVISOR_ID_COL]
                    if isinstance(supervisor_id, numbers.Number):
                        supervisor_id = str(int(supervisor_id))
                    supervisor = services.participants.find(
                        participant_id=supervisor_id,
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
            if _is_valid(gender_spec) and gender_spec[:1].upper() in \
                    APPLICABLE_GENDERS:
                participant.gender = gender_spec[:1].upper()
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

        if LOCALE_COL:
            selected_locale = record[LOCALE_COL]
            if _is_valid(selected_locale) and selected_locale in locales:
                participant.locale = selected_locale

        # save if this is a new participant - we need an id for lookup
        if not participant.id:
            participant.save()

        if phone_columns:
            # If this is an update for the participant, we should clear
            # the current list of phone numbers and then recreate them
            if participant.id:
                participant.phone_contacts = []
                db.session.commit()

            # check if the phone number is on record
            # import phone numbers in reverse order so the first is the latest
            for column in reversed(phone_columns):
                if not _is_valid(record[column]):
                    continue

                mobile = record[column]
                if isinstance(mobile, numbers.Number):
                    mobile = int(mobile)
                mobile_num = str(mobile)

                phone = services.phone_contacts.lookup(mobile_num, participant)
                if not phone:
                    phone = services.phone_contacts.create(
                        number=mobile_num, participant_id=participant.id,
                        verified=True)

        if sample_columns:
            for column in sample_columns:
                if not _is_valid(record[column]):
                    continue

                sample = sample_map.get(column)
                if sample is None:
                    continue

                try:
                    value = int(record[column])
                    if value == 0:
                        continue
                except ValueError:
                    continue
                participant.samples.append(sample)

        # sort out any extra fields
        extra_data = {}
        for field_name in extra_field_names:
            column = header_map.get(field_name)
            if column:
                value = record[column]
                if _is_valid(value):
                    if isinstance(value, numbers.Number):
                        value = int(value)
                    extra_data[field_name] = value

        # finally done with first pass
        participant.save()
        processed_records += 1

        # if we have extra data, update the participant
        if extra_data:
            services.participants.find(id=participant.id).update(
                {'extra_data': extra_data}, synchronize_session=False)

        task.update_task_info(
            total_records=total_records,
            error_records=error_records,
            processed_records=processed_records,
            warning_records=warning_records,
            error_log=error_log
        )

    # second pass - resolve missing supervisor references
    for participant_id, supervisor_id in unresolved_supervisors:
        try:
            participant_id = str(int(participant_id))
            supervisor_id = str(int(supervisor_id))
        except (TypeError, ValueError):
            continue

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
                gettext(
                    'Supervisor with ID %(id)s not found', id=supervisor_id)))
            processed_records -= 1
            error_records += 1
            error_log.append({
                'label': 'ERROR',
                'message': gettext(
                    'Supervisor ID %(sup_id)s specified for '
                    'participant ID %(part_id)s not found',
                    sup_id=supervisor_id, part_id=participant_id)
            })
            task.update_task_info(
                total_records=total_records,
                error_records=error_records,
                processed_records=processed_records,
                warning_records=warning_records,
                error_log=error_log
            )
        else:
            participant.supervisor_id = supervisor.id
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


@celery.task(bind=True)
def import_participants(
        self, upload_id, mappings, participant_set_id, channel=None):
    upload = services.user_uploads.find(id=upload_id).first()
    if not upload:
        logger.error('Upload %s does not exist, aborting', upload_id)
        return

    filepath = uploads.path(upload.upload_filename)
    if not os.path.exists(filepath):
        logger.error('Upload file %s does not exist, aborting', filepath)
        upload.delete()
        return

    with open(filepath, 'rb') as f:
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
        participant_set,
        self
    )

    # delete uploaded file
    os.remove(filepath)
    upload.delete()

    msg_body = generate_response_email(count, errors, warnings)

    send_email(_('Import report'), msg_body, [upload.user.email])


def _cleanup_upload(filepath, upload):
    os.remove(filepath)
    upload.delete()
