# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.participants.rmodels import (
    Participant, ParticipantGroup, ParticipantGroupType, ParticipantPartner)


class ParticipantService(Service):
    __model__ = Participant


class ParticipantGroupService(Service):
    __model__ = ParticipantGroup


class ParticipantGroupTypeService(Service):
    __model__ = ParticipantGroupType


class ParticipantPartnerService(Service):
    __model__ = ParticipantPartner
