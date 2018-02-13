# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.participants.models import (
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner,
    ParticipantRole)


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
