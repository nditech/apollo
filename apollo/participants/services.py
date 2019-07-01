# -*- coding: utf-8 -*-
import csv
from io import StringIO
import re

from apollo import constants
from apollo.core import db
from apollo.dal.service import Service
from apollo.locations.models import Location
from apollo.participants.models import (
    ParticipantSet,
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner,
    ParticipantRole, PhoneContact)

number_regex = re.compile('[^0-9]')


class ParticipantSetService(Service):
    __model__ = ParticipantSet


class ParticipantService(Service):
    __model__ = Participant

    def export_list(self, query):
        participant = query.first()
        participant_set = participant.participant_set
        location_set = participant_set.location_set

        location_types = location_set.location_types

        # build headers
        headers = ['ID', 'Name', 'Partner', 'Role', 'Location ID']
        headers.extend(lt.name for lt in location_types)

        headers.extend([
            'Supervisor ID', 'Gender', 'Email', 'Password',
            'Phone #1', 'Phone #2', 'Phone #3'
        ])

        samples = location_set.samples
        headers.extend(s.name for s in samples)

        # TODO: extra fields missing
        output_buffer = StringIO()
        output_buffer.write(constants.BOM_UTF8_STR)
        writer = csv.writer(output_buffer)

        writer.writerow(headers)
        yield output_buffer.getvalue()
        output_buffer.close()

        for participant in query:
            phones = participant.phone_contacts
            if phones:
                phone_numbers = [p.number for p in phones[:3]]
                phone_numbers += [''] * (3 - len(phone_numbers))
            else:
                phone_numbers = ['', '', '']

            record = [
                participant.participant_id,
                participant.name,
                participant.partner.name if participant.partner else '',
                participant.role.name if participant.role else '',
                participant.location.code,
            ]

            name_path = participant.location.make_path() \
                if participant.location else {}
            record.extend(name_path.get(lt.name, '') for lt in location_types)

            record.extend([
                participant.supervisor.participant_id
                if participant.supervisor else '',
                participant.gender.value if participant.gender else '',
                participant.email,
                participant.password
            ])

            record.extend(phone_numbers)

            for sample in samples:
                subquery = Location.query.filter(
                    Location.id == participant.location_id,
                    Location.samples.contains(sample))
                record.append(
                    int(db.session.query(subquery.exists()).scalar()))

            # TODO: process extra fields here
            output_buffer = StringIO()
            writer = csv.writer(output_buffer)
            writer.writerow(record)
            yield output_buffer.getvalue()
            output_buffer.close()


class ParticipantGroupService(Service):
    __model__ = ParticipantGroup


class ParticipantGroupTypeService(Service):
    __model__ = ParticipantGroupType


class ParticipantPartnerService(Service):
    __model__ = ParticipantPartner


class ParticipantRoleService(Service):
    __model__ = ParticipantRole


class PhoneContactService(Service):
    __model__ = PhoneContact

    def lookup(self, number, participant):
        num = number_regex.sub('', number)
        return self.__model__.query.filter_by(
            participant_id=participant.id,
            number=num
        ).first()
