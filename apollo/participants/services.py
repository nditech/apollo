# -*- coding: utf-8 -*-
import re

from apollo.dal.service import Service
from apollo.participants.models import (
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner,
    ParticipantPhone, ParticipantRole, Phone)

number_regex = re.compile('^[0-9]')


class ParticipantService(Service):
    __model__ = Participant


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
