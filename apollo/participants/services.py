# -*- coding: utf-8 -*-
import csv
from io import StringIO
import re

from apollo.dal.service import Service
from apollo.participants.models import (
    ParticipantSet,
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner,
    ParticipantPhone, ParticipantRole, Phone)

number_regex = re.compile('[^0-9]')


class ParticipantSetService(Service):
    __model__ = ParticipantSet


class ParticipantService(Service):
    __model__ = Participant

    def export_list(self, query):
        headers = [
            'ID', 'Name', 'Partner', 'Role', 'Location ID',
            'Supervisor ID', 'Gender', 'Email', 'Password',
            'Phone #1', 'Phone #2', 'Phone #3'
        ]

        # TODO: location data missing
        # TODO: extra fields missing
        output_buffer = StringIO()
        writer = csv.writer(output_buffer)

        writer.writerow(headers)
        yield output_buffer.getvalue()
        output_buffer.close()

        for participant in query:
            phones = participant.phones
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
                # TODO: insert location tree here
                participant.gender,
                participant.email,
                participant.password
            ]

            record.extend(phone_numbers)

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


class PhoneService(Service):
    __model__ = Phone

    def get_by_number(self, number):
        num = number_regex.sub('', number)
        return self.__model__.query.filter_by(number=num).first()


class ParticipantPhoneService(Service):
    __model__ = ParticipantPhone
