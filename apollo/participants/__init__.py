from tablib import Dataset
from ..core import Service
from .models import (
    Participant, ParticipantRole, ParticipantPartner, ParticipantGroup,
    ParticipantGroupType
)


class ParticipantsService(Service):
    __model__ = Participant

    def export_list(self, queryset):
        ds = Dataset(
            headers=[
                'Participant ID', 'Name', 'Role', 'Partner',
                'Location ID', 'Supervisor ID', 'Gender', 'Email', 'Phone'
            ]
        )

        for participant in queryset:
            # limit to three numbers for export and pad if less than three
            record = [
                participant.participant_id,
                participant.name,
                participant.role.name,
                participant.partner.name if participant.partner else '',
                participant.location.code if participant.location else '',
                participant.supervisor.participant_id if participant.supervisor else '',
                participant.gender,
                participant.email,
                participant.phone
            ]

            ds.append(record)

        return ds


class ParticipantRolesService(Service):
    __model__ = ParticipantRole


class ParticipantPartnersService(Service):
    __model__ = ParticipantPartner


class ParticipantGroupsService(Service):
    __model__ = ParticipantGroup


class ParticipantGroupTypesService(Service):
    __model__ = ParticipantGroupType
