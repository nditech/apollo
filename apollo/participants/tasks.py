from flask import render_template_string
from flask.ext.babel import lazy_gettext as _
from mongoengine import MultipleObjectsReturned
import pandas as pd
from ..messaging.tasks import send_email
from .. import services, helpers
from .models import PhoneContact


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


def create_partner(name, deployment):
    return services.participant_partners.create(name=name,
                                                deployment=deployment)


def create_group(name, deployment):
    return services.participant_groups.create(name=name,
                                              deployment=deployment)


def create_role(name, deployment):
    return services.participant_roles.create(name=name,
                                             deployment=deployment)


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
    NAME_COL = header_map['name']
    ROLE_COL = header_map['role']
    PARTNER_COL = header_map['partner_org']
    LOCATION_ID_COL = header_map['location_id']
    SUPERVISOR_ID_COL = header_map['supervisor_id']
    GENDER_COL = header_map['gender']
    EMAIL_COL = header_map['email']
    PHONE_PREFIX = header_map['phone']
    GROUP_PREFIX = header_map['group']

    phone_columns = [c for c in dataframe.columns
                     if c.startswith(PHONE_PREFIX)]
    group_columns = [c for c in dataframe.columns
                     if c.startswith(GROUP_PREFIX)]

    # create the groups
    for column in group_columns:
        group = services.participant_groups.get(name__iexact=column)
        if not group:
            create_group(column, event.deployment)

    for idx in index:
        record = dataframe.ix[idx]
        participant = services.participants.get(
            participant_id=record[PARTICIPANT_ID_COL],
            deployment=event.deployment,
            event=event
        )

        if participant is None:
            participant = services.participants.new(
                participant_id=record[PARTICIPANT_ID_COL],
                deployment=event.deployment,
                event=event
            )

        participant.name = record[NAME_COL]

        role = services.participant_roles.get(
            name=record[ROLE_COL],
            deployment=deployment
        )
        if role is None:
            role = create_role(record[ROLE_COL], deployment)
        participant.role = role

        partner = None
        if record[PARTNER_COL]:
            partner = services.participant_partners.get(
                name=record[PARTNER_COL],
                deployment=deployment
            )
            if partner is None:
                partner = create_partner(record[PARTNER_COL], deployment)
        participant.partner = partner

        location = None
        try:
            location = services.locations.get(
                code=record[LOCATION_ID_COL],
                deployment=deployment
            )
        except MultipleObjectsReturned:
            errors.add((
                record[PARTICIPANT_ID_COL],
                _('Invalid location id (%(loc_id)s)',
                    loc_id=record[LOCATION_ID_COL])
            ))
            continue

        if location is None:
            warnings.add((
                record[PARTICIPANT_ID_COL],
                _('Location with id %(loc_id)s not found',
                    loc_id=record[LOCATION_ID_COL])
            ))
        else:
            # explicitly set the location name path
            participant.location_name_path = {
                l.location_type: l.name for l in location.ancestors_ref}
        participant.location = location

        supervisor = None
        if record[SUPERVISOR_ID_COL]:
            if record[SUPERVISOR_ID_COL] != record[PARTICIPANT_ID_COL]:
                # ignore cases where participant is own supervisor
                supervisor = services.participants.get(
                    participant_id=record[SUPERVISOR_ID_COL],
                    event=event
                )
                if supervisor is None:
                    # perhaps supervisor exists further along. cache the refs
                    unresolved_supervisors.add(
                        (record[PARTICIPANT_ID_COL], record[SUPERVISOR_ID_COL])
                    )
        participant.supervisor = supervisor

        participant.gender = record[GENDER_COL]

        participant.email = record[EMAIL_COL]

        # wonky hacks to avoid doing addToSet queries
        # for events and phone numbers
        phone_info = {}
        for phone in participant.phones:
            phone_info[phone.number] = phone.verified
        for column in phone_columns:
            if not record[column]:
                continue
            pn = unicode(record[column])
            phone_info[pn] = True

        participant.phones = [
            PhoneContact(number=unicode(k),
                         verified=v) for k, v in phone_info.items()
        ]

        # fix up groups
        for column in group_columns:
            group = services.participant_groups.get(
                name=column,
                deployment=event.deployment
            )

            if pd.isnull(record[column]) or not record[column]:
                continue

            group.update(add_to_set__tags=record[column])

            d = set(participant.group_tags)
            d.add(record[column])

            participant.group_tags = list(d)

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
