from ..core import Service
from .models import Participant, ParticipantRole, ParticipantPartner


class ParticipantsService(Service):
    __model__ = Participant


class ParticipantRolesService(Service):
    __model__ = ParticipantRole


class ParticipantPartnersService(Service):
    __model__ = ParticipantPartner
