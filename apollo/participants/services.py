# -*- coding: utf-8 -*-
import csv
from io import StringIO
import re

from flask_babelex import gettext as _
from sqlalchemy import and_, case, exists, false, select, true

from apollo import constants
from apollo.dal.service import Service
from apollo.participants.models import (
    ParticipantSet,
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner,
    ParticipantRole, PhoneContact, Sample, samples_participants)

number_regex = re.compile('[^0-9]')


class ParticipantSetService(Service):
    __model__ = ParticipantSet


class ParticipantService(Service):
    __model__ = Participant

    def export_list(self, query):
        if query.count() == 0:
            raise StopIteration

        participant = query.first()
        participant_set = participant.participant_set
        location_set = participant_set.location_set

        location_types = location_set.location_types

        # build headers
        headers = [
            _('Participant ID'), _('Full Name'), _('First Name'),
            _('Other Names'), _('Last Name'), _('Partner'), _('Role'),
            _('Location Code')]
        headers.extend(lt.name for lt in location_types)

        headers.extend([
            _('Supervisor ID'), _('Gender'), _('Email'), _('Password'),
            _('Phone #1'), _('Phone #2'), _('Phone #3')
        ])

        samples = participant_set.samples.order_by(Sample.name)
        headers.extend(s.name for s in samples)

        sample_subqueries = []
        for sample in samples:
            condition = exists(select(
                [samples_participants.c.sample_id]
            ).where(and_(
                samples_participants.c.participant_id == Participant.id,
                samples_participants.c.sample_id == sample.id
            )))
            sample_subqueries.append(case([
                (condition == true(), 1),
                (condition == false(), 0),
            ]))

        columns = [Participant] + sample_subqueries
        query2 = query.with_entities(*columns)
        sample_indices = range(1, samples.count() + 1)

        # TODO: extra fields missing
        output_buffer = StringIO()
        output_buffer.write(constants.BOM_UTF8_STR)
        writer = csv.writer(output_buffer)

        writer.writerow(headers)
        yield output_buffer.getvalue()
        output_buffer.close()

        for row in query2:
            participant = row[0]
            phones = participant.phones
            if phones:
                phone_numbers = [p.number for p in phones[:3]]
                phone_numbers += [''] * (3 - len(phone_numbers))
            else:
                phone_numbers = ['', '', '']

            record = [
                participant.participant_id,
                participant.full_name,
                participant.first_name,
                participant.other_names,
                participant.last_name,
                participant.partner.name if participant.partner else '',
                participant.role.name if participant.role else '',
                participant.location.code if participant.location else '',
            ]

            name_path = participant.location.make_path() \
                if participant.location else {}
            record.extend(name_path.get(lt.name, '') for lt in location_types)

            record.extend([
                participant.supervisor.participant_id
                if participant.supervisor else '',
                participant.gender.code if participant.gender else '',
                participant.email,
                participant.password
            ])

            record.extend(phone_numbers)

            for index in sample_indices:
                record.append(row[index])

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
